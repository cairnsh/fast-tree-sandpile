# fastsand version 1.0
# Python 2.7.10
import btree

class tree:
    def __init__(self, parent):
        """There are len(parent) vertices. The root is always at vertex 0.
        parent[j] is the parent of vertex j. parent[0] is ignored."""
        self.parent = parent[:]
        self.size = len(self.parent)
        self.children = {}
        self.data = {}
        for i in xrange(self.size):
            self.children[i] = []
        self.nchildren = [1] * self.size
        # iya
        for i in xrange(1, self.size):
            self.children[self.parent[i]].append(i)
        for i in xrange(self.size - 1, 0, -1):
            self.nchildren[self.parent[i]] += self.nchildren[i]

    def get_nchildren(self, j):
        return self.nchildren[j]

    def get_children(self, j): return self.children[j][:]

    def get_degree(self, j):
        return len(self.children[j])

    def get_data(self, j):
        return self.data.get(j, None)

    def set_data(self, j, x):
        self.data[j] = x

    def descendants(self, j, postorder=False):
        "Don't use recursion, because the tree might be deep and Python has a stack limit"
        tree = [j]
        back = [-1]
        if not postorder:
            yield j
        while tree:
            back[-1] += 1
            children = self.children[tree[-1]]
            if back[-1] >= len(children):
                if postorder:
                    yield tree[-1]
                del tree[-1]
                del back[-1]
            else:
                child = children[back[-1]]
                if not postorder:
                    yield child
                tree.append(child)
                back.append(-1)

    def combine(self, fn, root=0):
        for child in self.descendants(root, True):
            fn(child)

    def uncombine(self, fn, root=0):
        for child in self.descendants(root, False):
            fn(child)

class label_record:
    def __init__(self):
        self.la = {}
    def add(self, x):
        self.la[x.label] = x
    def delete(self, x):
        del self.la[x.label]
    def get_vertex_with_label(self, label):
        return self.la.get(label, None)

class sandpile_tree:
    def __init__(self, parent, chipcount):
        self.tree = tree(parent)
        self.chipcount = chipcount[:]
        self.labelrec = label_record()
        self.stable = True
        self.operation_counts = [0, 0, 0, 0]

    def STRETCH(self, plain_labeling):
        plain_labeling.add_poly_to(1, 1)

    def UNSTRETCH(self, plain_labeling):
        plain_labeling.add_poly_to(-1, -1)

    def MERGE(self, plain_labeling, b):
        self.operation_counts[0] += b.size()
        plain_labeling.add_all_of(b)

    def ADD_ZERO(self, main, lab):
        #print "ADD ZERO"
        r = btree.node(0, lab)
        self.labelrec.add(r)
        main.add(r)
        pass

    def FIRST(self, main):
        self.operation_counts[2] += 1; return main.first()

    def REPEATED_CHIP_ADD_OPERATION(self, n, main):
        flow = 0
        #print "REPEATED CHIP ADD"
        while n > 0:
            first = self.FIRST(main)
            if first is None:
                flow += n
                break
            if n < first.val:
                main.add_poly_to(0, -n)
                flow += n
                break
            x = first.val
            main.add_poly_to(0, -x)
            n -= x
            flow += x
            "The first entry is now zero."
            if n > 0:
                first = self.FIRST(main)
                self.POP(main, first)
                n -= 1
        return flow

    def SANDPILE_CHIP_ADD_OPERATION(self, n, main):
        for i in range(n):
            first = self.FIRST(main)
            if first is None:
                return True
            self.POP(main, first)
        # execute rounds until subcritical
        first = self.FIRST(main)
        if first is None:
            return True
        main.add_poly_to(0, -first.val)
        return False

    def DESTRUCTIVE_GET_DATA_TREE(self, j):
        data = self.tree.get_data(j)
        assert(len(data) == 2)
        (tree, flow) = data
        data[:] = []
        return (tree, flow)

    def DESTRUCTIVE_GET_DATA_CHIP(self, j):
        data = self.tree.get_data(j)
        assert(len(data) == 1)
        (chips,) = data
        data[:] = []
        return chips

    def SET_DATA_TREE(self, j, tree, flow):
        self.tree.set_data(j, [tree, flow])

    def SET_DATA_CHIP(self, j, chips):
        self.tree.set_data(j, [chips])

    def POP(self, tree, first):
        self.operation_counts[3] += 1
        tree.delete_first()
        self.labelrec.delete(first)

    def DELETE_LEADING_ZEROES(self, tree):
        n = 0
        while True:
            first = self.FIRST(tree)
            if first and first.val == 0:
                self.POP(tree, first)
                n += 1
            else:
                break
        return n

    def EXTRACT_ALL_CHILDREN(self, tree, j):
        small = btree.btree()
        iter = self.tree.descendants(j)
        iter.next() # throw away root
        for child in iter:
            self.operation_counts[1] += 1
            node = self.labelrec.get_vertex_with_label(child)
            if node:
                if not tree.delete_object(node):
                    print node, tree.serialize()
                    raise Exception("could not find node")
                small.add(node)
        return small

    def sort_children(self, j):
        children = self.tree.get_children(j)
        children.sort(key=lambda x: -self.tree.get_nchildren(x))
        return children

    def combiner(self, j, sandpile_at_root=False):
        children = self.sort_children(j)
        C = 0
        if children:
            (main, flow) = self.DESTRUCTIVE_GET_DATA_TREE(children[0])
            self.STRETCH(main)
            C += flow
            for other in children[1:]:
                (small, flow) = self.DESTRUCTIVE_GET_DATA_TREE(other)
                C += flow
                self.STRETCH(small)
                self.MERGE(main, small)
        else:
            main = btree.btree()
        C += self.DESTRUCTIVE_GET_DATA_CHIP(j)
        C -= self.tree.get_degree(j)
        flow = 0
        if C < 0:
            for i in range(-C):
                "Use the labels of the children for uniqueness."
                self.ADD_ZERO(main, children[i])
        elif C >= 0:
            if j != 0 or not sandpile_at_root:
                flow = self.REPEATED_CHIP_ADD_OPERATION(C, main)
            else:
                self.stable = not self.SANDPILE_CHIP_ADD_OPERATION(C, main)
        
        self.SET_DATA_TREE(j, main, flow)

    def combiner_not_at_root(self, j):
        self.combiner(j, True)

    def plain_labeling(self, combiner=None):
        if combiner is None:
            combiner = self.combiner
        for j in xrange(self.tree.size):
            self.SET_DATA_CHIP(j, self.chipcount[j])
        self.tree.combine(combiner)
        return self.tree.get_data(0)
        
    def uncombiner(self, j):
        children = self.sort_children(j)
        (tree, flow) = self.DESTRUCTIVE_GET_DATA_TREE(j)
        nzeroes = self.DELETE_LEADING_ZEROES(tree)
        self.SET_DATA_CHIP(j, self.tree.get_degree(j) - nzeroes)
        if children:
            for other in children[1:]:
                small = self.EXTRACT_ALL_CHILDREN(tree, other)
                self.UNSTRETCH(small)
                self.SET_DATA_TREE(other, small, 0)
            self.UNSTRETCH(tree)
            self.SET_DATA_TREE(children[0], tree, 0)

    def reconstruct_chips(self):
        self.tree.uncombine(self.uncombiner)
        for j in xrange(self.tree.size):
            self.chipcount[j] = self.DESTRUCTIVE_GET_DATA_CHIP(j)

    def stabilize_rpile_style(self):
        self.plain_labeling(self.combiner)
        self.reconstruct_chips()
        return self.chipcount

    def stabilize(self):
        x = self.plain_labeling(self.combiner_not_at_root)
        self.reconstruct_chips()
        return self.stable and self.chipcount

    def stats(self):
        return self.operation_counts[:]

def plain_labeling(t, c):
    pile = sandpile_tree(t, c)
    return tuple(pile.plain_labeling(pile.combiner_not_at_root)[0].traverser())

def stabilize(t, c):
    pile = sandpile_tree(t, c)
    return pile.stabilize(), pile.stats()

def topple(t, c, i):
    children = t.get_children(i)
    if i != 0:
        children.append(t.parent[i])
    if c[i] < len(children):
        return False
    for child in children:
        c[child] += 1
    c[i] -= len(children)
    return True

def simulation_stabilize(t, c):
    t = tree(t)
    chips = c[:]
    stable = False
    if sum(chips) >= t.size - 1:
        return False
    j = 0
    while not stable:
        stable = True
        j += 1
        for i in range(t.size):
            if topple(t, chips, i):
                stable = False
    return chips

def testone(t, c):
    tree = (t, c)
    print plain_labeling(*tree)
    s1 = stabilize(*tree)
    s2 = simulation_stabilize(*tree)
    print "tree: %s" % str(tree)
    print "stabilization: %s" % str(s1)
    print "simulation stabilization: %s" % str(s2)
    print "equal: %s" % str(tuple(s1) == tuple(s2))

def tesu():
    testone([0, 0, 1, 2, 3, 1, 5, 6, 7, 1, 9, 10, 11, 12],
            [0, 0, 0, 1, 2, 1, 0, 0, 0, 0, 0, 6, 0, 0])
    testone([0, 0, 0, 0, 2, 3, 3, 1, 4, 8, 5, 4, 11, 9, 1,
             13, 1, 12, 2, 5, 14, 19, 5, 19, 22, 5, 5, 9, 20,
             1, 20, 1, 17, 29, 26, 27, 32, 24, 15, 24, 30],
            [0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1,
             1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0,
             0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1])

def random_tree(n, output=None, zero=0):
    import random
    n -= 1
    def r():
        walk = [1] * n + [-1] * (n-1)
        random.shuffle(walk)
        return walk
    walk = r()
    total = 0
    minimum = 0
    minindx = 0
    for i in range(2*n - 1):
        total += walk[i]
        if total <= minimum:
            minimum = total
            minindx = i
    walk = walk[minindx:] + walk[:minindx]
    stack = [0]
    tree = [0]
    cur = 0
    for i in range(1,2*n-1):
        if walk[i] == +1:
            cur += 1
            tree.append(stack[-1])
            stack.append(cur)
        else:
            stack.pop(-1)
    return tree

def random_tree_2(n):
    foo = [0]
    for j in range(3000):
        bar.append(random.randint(0, j))

def balanced_tree(n):
    foo = [0] + [x >> 1 for x in range(n-1)]
    return foo

def worstcost(SIZE):
    if SIZE <= 3:
        return 0
    return 2*worstcost((SIZE-1)/2) + max((SIZE - 1)/2, 0)

def test():
    import random, math, time
    SIZE = 4096
    SLS2 = math.ceil(SIZE * (math.log(SIZE, 2)) * 0.5)
    print """This test generates random trees, adds a large number of chips to one
vertex, and compares the results of fast and slow stabilization. If there is
a problem (the fast algorithm does more work than it is guaranteed to do, or
the results of the two algorithms are not equal) it will throw an exception.

Note: the slow stabilization is written in the simplest possible way, so the
speed comparison is not really fair. It is just there to make sure that the
fast stabilization works (or at least gets the same result as the completely
different method used in the slow stabilization).

The trees are size %d. Here is the meaning of the counters:
merge    | How many entries are added in merging?          | Maximum: %d
extract  | How many entries are extracted in unmerging?    | Maximum: %d
first    | How many times do we look at the first element? | Maximum: %d
pop      | How many times do we pop the first element?     | Maximum: %d\n""" % (SIZE, SLS2, SLS2, SIZE * 3, SIZE)
    for i in range(SIZE):
        bar = [0]
        foo = [0] * SIZE
        #bar = random_tree(SIZE)
        nchips = random.randint(0, SIZE)
        overfull = random.random() < 0.04
        if overfull:
            nchips = 2 * SIZE
        random_or_balanced = random.random() > 0.2
        bar = (random_or_balanced and random_tree or balanced_tree)(SIZE)
        random_or_balanced_text = random_or_balanced and "Uniformly random plane tree" or "Balanced tree"
        foo[random.randint(0, SIZE)] = nchips
        tree = (bar, foo)
        print "#%d. %s. Chips = %d." % (i, random_or_balanced_text, nchips)
        print "starting fast stabilization...",
        t1 = time.clock()
        s1, stats = stabilize(*tree)
        t2 = time.clock() - t1
        print "%.2f seconds" % t2
        def compare_to_sls(x):
            if x > SLS2:
                raise Exception("Too many merge/extract operations: there should only be 1/2 n lg n")
            else:
                return "%d (%2.0f%%)" % (x, 100.0*x/float(SLS2))
        def compare_to_s(x, n):
            if x > SIZE * n:
                raise Exception("Too many first/pop operations: there should only be %dn" % n)
            else:
                return "%d (%2.0f%%)" % (x, 100.0*x/float(SIZE * n))
        print "merge %s; extract %s; first %s; pop %s" % (tuple(map(compare_to_sls, stats[0:2])) + (compare_to_s(stats[2], 3), compare_to_s(stats[3], 1)))
        print "starting slow stabilization...",
        import sys
        sys.stdout.flush()
        t1 = time.clock()
        s2 = simulation_stabilize(*tree)
        t2 = time.clock() - t1
        print "%.2f seconds" % t2
        if isinstance(s1, list):
            s1 = tuple(s1)
        if isinstance(s2, list):
            s2 = tuple(s2)
        if s1 != s2:
            print "tree: %s" % str(tree)
            print "stabilization: %s" % str(s1)
            print "simulation stabilization: %s" % str(s2)
            raise Exception("failure")
        print "The stabilizations are equal.\n"
    return
    bar = [0] + [x for x in range(12)]
    foo = [0] * 13
    foo[6] = 1
    for i in range(14):
        tree = (bar, foo)
        foo[7] = i
        print stabilize(*tree)
        print simulation_stabilize(*tree)

def speedtest():
    import random
    for i in range(12):
        bar = [0]
        foo = [0]
        for j in range(30000):
            bar.append(random.randint(0, j))
            chips = 0
            while random.random() > 0.6:
                chips += 1
            foo.append(chips)
        tree = (bar, foo)
        s1 = stabilize(*tree)
        print "speedtest: tree %2d finished" % i

def profile():
    import cProfile
    cProfile.run("speedtest()")

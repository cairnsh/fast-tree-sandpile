# btree version 1.0
# Python 2.7.10
"""This is an implementation of 2-4 B-trees in Python.
   It allows you to decorate nodes with extra data
   and run a callback when a node is touched."""

class node_allocator:
    def __init__(self):
        self.nodelist = {}
        self.node_id = 1
        self.nodesize = {}
        self.nodecoeffs = {}

    def alloc_node(self):
        j = self.node_id
        "node[0:7] = [child_id, data, child_id, data, child_id, data, child_id]"
        node = [0, None, 0, None, 0, None, 0, 0]
        self.nodelist[j] = node
        self.nodesize[j] = 0
        self.node_id += 1
        return j

    def free_node(self, j):
        del self.nodelist[j]
        del self.nodesize[j]

    def get_node(self, j):
        return self.nodelist[j]

    def get_size(self, j):
        return self.nodesize[j]

    def get_data(self, j):
        return self.nodelist[j][7]

    def set_data(self, j, x):
        self.nodelist[j][7] = x

    def add_size(self, j, delt):
        self.nodesize[j] += delt

    def update_sizes(self, *args):
        for j in args:
            node = self.nodelist[j]
            total = 0
            for x in range(7):
                if x & 1:
                    if node[x] is None:
                        break
                    total += 1
                else:
                    if node[x] != 0:
                        total += self.nodesize[node[x]]
            self.nodesize[j] = total

alloc = node_allocator()

class node_manager:
    def delink(self, up, node):
        for i in xrange(min(len(node), 7)):
            if i & 1:
                if node[i] is not None:
                    del up[node[i]]
                else:
                    break
            else:
                if node[i] is not 0:
                    del up[node[i]]
    def relink(self, up, j, node):
        for i in xrange(min(len(node), 7)):
            if i & 1:
                if node[i] is not None:
                    up[node[i]] = j
                else:
                    break
            else:
                if node[i] is not 0:
                    up[node[i]] = j
                    pass
    def setlink(self, up, key, node):
        up[key] = node
    def dellink(self, up, key):
        del up[key]
    def search(self, node, key):
        "Even return values mean that the key is in a child. Odd means the key is in the node."
        if node[1] is None:
            return 0
        x = cmp(key,node[1])
        if x < 0:
            return 0
        if x == 0:
            return 1
        if node[3] is None:
            return 2
        x = cmp(key, node[3])
        if x < 0:
            return 2
        if x == 0:
            return 3
        if node[5] is None:
            return 4
        x = -cmp(node[5], key)
        if x < 0:
            return 4
        if x == 0:
            return 5
        return 6
    def search_is_equality(self, node, key):
        "Search for object already in tree using is-comparison."
        if node[1] is None:
            return 0
        x = cmp(key,node[1])
        if x < 0:
            return 0
        if node[1] is key:
            return 1
        if node[3] is None:
            return 2
        x = cmp(key, node[3])
        if x < 0:
            return 2
        if node[3] is key:
            return 3
        if node[5] is None:
            return 4
        x = -cmp(node[5], key)
        if x < 0:
            return 4
        if node[5] is key:
            return 5
        return 6
    def srnif(self, up, j, node):
        "Split root node if full"
        if not nm.fullp(node):
            return False
        r1 = alloc.alloc_node()
        r2 = alloc.alloc_node()
        noder1 = alloc.get_node(r1)
        noder2 = alloc.get_node(r2)
        noder1[0:3] = node[0:3]
        noder2[0:3] = node[4:7]
        self.relink(up, r1, node[0:3])
        self.relink(up, r2, node[4:7])
        node[0:7] = [r1, node[3], r2, None, 0, None, 0]
        self.relink(up, j, node)
        alloc.update_sizes(r1, r2)
        return (r1, r2)
    def scnif(self, up, j, node, child_index):
        "Split child node if full"
        r1 = node[child_index]
        noder1 = alloc.get_node(r1)
        if not nm.fullp(noder1):
            return False
        r2 = alloc.alloc_node()
        noder2 = alloc.get_node(r2)
        extra = noder1[3]
        noder2[0:3] = noder1[4:7]
        self.relink(up, r2, noder2)
        noder1[3:7] = [None, 0, None, 0]
        node[child_index:7] = [r1, extra, r2] + node[child_index+1:5]
        self.relink(up, j, [r1, extra, r2])
        alloc.update_sizes(r1, r2)
        return True
    def insert_in_leaf(self, up, j, node, y, key):
        node[y+2:7] = node[y:5]
        node[y] = key
        self.setlink(up, key, j)
    def delete_from_leaf(self, up, j, node, y):
        self.dellink(up, node[y])
        node[y:7] = node[y+2:7] + [None, 0]
    def leafp(self, node):
        return node[0] == 0
    def fullp(self, node):
        return node[5] != None
    def IFKEYNEXTCHILD(self, x):
        return (x+1)&~1
    def NEXTKEY(self, x):
        return (x+1)|1
    def getchild(self, node, x):
        return node[x]
    def getkey(self, node, x):
        return node[x]
    def propagate_down(self, node):
        data = node[7]
        if not data:
            return
        size = 0
        for x in range(7):
            if not x&1:
                if node[x] == 0:
                    continue
                self.add_poly_to(node[x], data[0], data[0] * size + data[1])
                size += alloc.get_size(node[x])
            else:
                if node[x] is None:
                    break
                node[x] += data[0] * size + data[1]
                size += 1
        node[7] = 0
    def add_poly_to(self, j, a, b):
        data = alloc.get_data(j)
        if data:
            (A, B) = data
            (a, b) = (A+a, B+b)
        if a != 0 or b != 0:
            alloc.set_data(j, (a, b))
        else:
            alloc.set_data(j, 0)
    def merge(self, up, index, node, left, center, right, size_change):
        combine = left + [center] + right
        node[:len(combine)] = combine
        self.relink(up, index, node)
        alloc.add_size(index, size_change)

nm = node_manager()

class btree:
    DEBUG_ON = False
    def __init__(self):
        self.root = alloc.alloc_node()
        self.up = {}
        nm.setlink(self.up, self.root, None)
        self.DEBUG_LOG = []
    def __del__(self):
        for k in self.traverser():
            nm.dellink(self.up, k)
        nodes = list(self.traverser(return_keys = False, return_nodes = True))
        for n in nodes:
            nm.dellink(self.up, n)
            alloc.free_node(n)
    def splitroot(self, node):
        return nm.srnif(self.up, self.root, node)
    def split(self, index, node, childindex):
        self.get_node(nm.getchild(node, childindex))
        return nm.scnif(self.up, index, node, childindex)
    def get_up(self, x):
        return self.up[x]
    def get_node(self, j):
        node = alloc.get_node(j)
        nm.propagate_down(node)
        return node
    def add_poly_to(self, a, b):
        nm.add_poly_to(self.root, a, b)
    def add(self, key):
        nodeid = self.root
        node = self.get_node(nodeid)
        self.splitroot(node)
        while True:
            "The node should not be full at this point."
            alloc.add_size(nodeid, 1)
            childindex = nm.search(node, key)
            if nm.leafp(node):
                nm.insert_in_leaf(self.up, nodeid, node, nm.NEXTKEY(childindex), key)
                break
            else:
                if self.split(nodeid, node, nm.IFKEYNEXTCHILD(childindex)):
                    childindex = nm.search(node, key) # node changed, so search it again
                nodeid = nm.getchild(node, nm.IFKEYNEXTCHILD(childindex))
                node = self.get_node(nodeid)
    def first(self):
        node = self.get_node(self.root)
        while not nm.leafp(node):
            node = self.get_node(nm.getchild(node, 0))
        return nm.getkey(node, 1)
    def delete(self, key):
        def search_for_key(node):
            return nm.search(node, key)
        return self.gendel(search_for_key)
    def delete_first(self):
        def always_choose_first(node):
            if node[0] == 0 and node[1] is not None: # leaf node
                return 1
            return 0
        return self.gendel(always_choose_first)
    def delete_object(self, key):
        chain = []
        up = self.get_up(key)
        rebalance = []
        while up:
            chain.append(up)
            up = self.get_up(up)
        # Go down the chain creating the rebalance list
        # and pushing the polynomial coefficients down the
        # tree to the one we are searching for
        while chain:
            nodeid = chain.pop()
            node = self.get_node(nodeid)
            if chain:
                for i in range(0, 7, 2):
                    if node[i] == chain[-1]:
                        x = i
                rebalance.append((nodeid, x))
            else:
                x = nm.search_is_equality(node, key)
        if node[x] != key:
            return False
        self.delete_in_node(nodeid, x, rebalance)
        return True
    def DEBUG(self, x):
        if btree.DEBUG_ON:
            self.DEBUG_LOG.append(x)
            if len(self.DEBUG_LOG) > 30:
                self.DEBUG_LOG.pop(0)
    def gendel(self, chooser):
        def DEBUG(x):
            self.DEBUG(x)
        rebalance = []
        xx = self.root
        node = self.get_node(xx)
        while True:
            x = chooser(node)
            if x & 1:               break
            if node[x] == 0:
                return False
            rebalance.append((xx, x))
            xx = node[x]
            node = self.get_node(xx)
        self.delete_in_node(xx, x, rebalance)
        return True
    def delete_in_node(self, nodeid, childindex, rebalance):
        def DEBUG(x):
            self.DEBUG(x)
        node = self.get_node(nodeid)
        nextchildptr = nm.IFKEYNEXTCHILD(childindex)
        if node[nextchildptr] == 0:
            nm.delete_from_leaf(self.up, nodeid, node, childindex)
            alloc.add_size(nodeid, -1)
            leaf_node_was_empty = node[1] is None
        else:
            rebalance.append((nodeid, nextchildptr))
            nextnodeid = node[nextchildptr]
            nextnode = self.get_node(nextnodeid)
            while nextnode[0] != 0:
                rebalance.append((nextnodeid, 0))
                nextnodeid = nextnode[0]
                nextnode = self.get_node(nextnodeid)
            (node[childindex], nextnode[1]) = (nextnode[1], node[childindex])
            nm.delete_from_leaf(self.up, nextnodeid, nextnode, 1)
            alloc.add_size(nextnodeid, -1)
            nm.setlink(self.up, node[childindex], nodeid)
            leaf_node_was_empty = nextnode[1] is None
        for (childptr, childindex) in rebalance:
            alloc.add_size(childptr, -1)
        self.reba(rebalance, leaf_node_was_empty)
    def reba(self, rebalance, previous_node_too_small):
        "rebalance small nodes"
        def DEBUG(x):
            self.DEBUG(x)
        if not rebalance:
            return
        def two_or_smaller(node):
            "return True if the size of the node is <= 2"
            return node[3] is None
        up = self.up
        while rebalance and previous_node_too_small:
            (nodeid, childindex) = rebalance.pop()
            node = self.get_node(nodeid)
            if childindex == 0:
                (node1id, extra, node2id) = node[0:3]
                node1 = self.get_node(node1id) # small
                node2 = self.get_node(node2id)
                if two_or_smaller(node2): # second node is size 2: merge
                    nm.merge(up, node1id, node1, [node1[0]], extra, node2[0:3], size_change=alloc.get_size(node2id) + 1)
                    alloc.free_node(node2id)
                    nm.dellink(up, node2id)
                    node[1:7] = node[3:7] + [None, 0]
                else: # second node is size 3-4: steal
                    (node1[1], node1[2], node[1]) = (extra, node2[0], node2[1])
                    node2[0:7] = node2[2:7] + [None, 0]
                    nm.setlink(up, extra, node1id)
                    nm.setlink(up, node1[1], node1id)
                    nm.setlink(up, node1[2], node1id)
                    nm.setlink(up, node[1], nodeid)
                    stealsize = node1[2] and alloc.get_size(node1[2])
                    alloc.add_size(node1id, 1 + stealsize)
                    alloc.add_size(node2id, -1 - stealsize)
            else:
                (node1id, extra, node2id) = node[childindex-2:childindex+1]
                node1 = self.get_node(node1id)
                node2 = self.get_node(node2id) # small
                if two_or_smaller(node1): # first node is size 2: merge
                    nm.merge(up, node1id, node1, node1[0:3], extra, [node2[0]], size_change=alloc.get_size(node2id) + 1)
                    alloc.free_node(node2id)
                    nm.dellink(up, node2id)
                    node[childindex-1:7] = node[childindex+1:7] + [None, 0]
                else: # first node is size 3-4: steal
                    node2[1:3] = (extra, node2[0])
                    nm.setlink(up, extra, node2id)
                    if node1[5] is not None: # size 4
                        (node[childindex-1], node2[0]) = node1[5:7]
                        nm.setlink(up, node2[0], node2id)
                        nm.setlink(up, node[childindex-1], nodeid)
                        node1[5:7] = [None, 0]
                    else: # size 3
                        (node[childindex-1], node2[0]) = node1[3:5]
                        nm.setlink(up, node2[0], node2id)
                        nm.setlink(up, node[childindex-1], nodeid)
                        node1[3:5] = [None, 0]
                    stealsize = node2[0] and alloc.get_size(node2[0])
                    alloc.add_size(node1id, -1 - stealsize)
                    alloc.add_size(node2id, 1 + stealsize)
            if node[1] is not None:
                previous_node_too_small = False
        if previous_node_too_small:
            # The root is too small.
            x = node[0]
            if x != 0:
                node2 = self.get_node(x)
                node[:] = node2[:]
                nm.relink(up, self.root, node)
                alloc.free_node(x)
        
    def traverser(self, return_keys = True, return_nodes = False):
        self.back = [-1]
        self.tree = [self.root]
        if return_nodes:
            yield self.root
        while self.tree:
            self.back[-1] += 1
            j = self.tree[-1]
            node = self.get_node(j)
            x = self.back[-1]
            if x & 1:
                if x == 7 or node[x] is None: # back up
                    del self.back[-1]
                    del self.tree[-1]
                    continue
                if return_keys:
                    yield node[x]
            else:
                if node[x] != 0:
                    if return_nodes:
                        yield node[x]
                    self.back.append(-1)
                    self.tree.append(node[x])
    def serialize(self, j=0):
        if not j:
            return self.serialize(self.root)
        node = alloc.get_node(j)
        serialization = [node[7]]
        for i in range(7):
            if i & 1 and node[i] is not None:
                serialization.append(node[i])
            if not i & 1 and node[i] != 0:
                serialization.append(self.serialize(node[i]))
        return serialization
    def add_all_of(self, tree):
        for node in tree.traverser():
            self.add(node)
    def size(self):
        return alloc.get_size(self.root)

class node:
    def __init__(self, val, label):
        self.val = val
        self.label = label
    def add(self, j):
        self.val += j
    def __cmp__(a, b):
        if b is None:
            return 1
        return cmp(a.val, b.val)
    def __eq__(a, b):
        if isinstance(b, node):
            return a.val == b.val
        else:
            return False
    def __ne__(a, b):
        return not a.__eq__(b)
    def __repr__(self):
        return "%d_%s" % (self.val, str(self.label))
    def __iadd__(a, b):
        "You can add an int to the value. Used in btree.add_poly_to."
        if not isinstance(b, int):
            raise TypeError("unsupported operator types for +=: '%s' and '%s'" % (type(a), type(b)))
        a.val += b
        return a
    def __hash__(self):
        return id(self)

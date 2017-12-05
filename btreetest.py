# btreetest version 1.0
# Python 2.7.10
from btree import btree, node, alloc, nm
import unittest
import random

def random_node():
    return node(random.randint(0, 999999), random.randint(0, 999999))

def random_node_object():
    return node(random.randint(0, 12), 0)

class TestAddDelete(unittest.TestCase):
    def test_add(self):
        x = btree()
        l = [random_node() for j in range(60)]
        for i in l:
            x.add(i)
        self.assertTrue(tuple(x.traverser()) == tuple(sorted(l)))

    def checknodesizes(self, x):
        r = x.traverser(return_keys = False, return_nodes = True)
        for j in r:
            size = alloc.nodesize[j]
            alloc.update_sizes(j)
            size2 = alloc.nodesize[j]
            if size != size2:
                return False
        return True

    def checkup(self, x):
        r = x.traverser(return_keys = True, return_nodes = True)
        problem = False
        for j in r:
            up = x.get_up(j)
            if up is not None and j not in alloc.get_node(up):
                print "problem with node %s: %d %s" % (str(j), up,
                                                    str(alloc.get_node(up)))
                problem = True
        return not problem

    def tad(self, use_delete_object=False, check_node_sizes=False,
              check_up=False):
        x = btree()
        if use_delete_object:
            rnf = random_node_object
        else:
            rnf = random_node
        l = [rnf() for j in range(60)]
        for i in l:
            x.add(i)
        for i in range(6000):
            if l and random.random() > 0.499:
                if use_delete_object:
                    if not x.delete_object(l[0]):
                        raise Exception("failed to delete")
                    if l[0] in x.up:
                        print "deleting %s %s" % (l[0], x.up)
                        raise Exception("up is leaking")
                else:
                    x.delete(l[0])
                del l[0]
            elif l:
                r = rnf()
                l.append(r)
                x.add(r)
            else:
                l = [rnf() for j in range(60)]
                for j in l:
                    x.add(j)
            if (i%4 == 0) and tuple(x.traverser()) != tuple(sorted(l)):
                return False
            if (i%12 == 0) and check_node_sizes:
                self.assertTrue(self.checknodesizes(x))
            if check_up:
                self.assertTrue(self.checkup(x))
        return True

    def test_add_delete(self):
        self.tad()
    
    def test_add_delete_object(self):
        self.tad(True)
    
    def test_add_delete_check_node_sizes(self):
        self.tad(False, True)
    
    def test_add_delete_object_check_node_sizes(self):
        self.tad(True, True)

    def test_add_delete_check_up(self):
        self.tad(False, False, True)

def test():
    import random
    x = btree()
    l = []
    for i in range(60):
        r = random.randint(0, 999999)
        l.append(r)
        x.add(r)
        if tuple(x.traverser()) != tuple(sorted(l)):
            break
    random.shuffle(l)
    def checknodesizes():
        r = x.traverser(return_keys = False, return_nodes = True)
        for j in r:
            size = alloc.nodesize[j]
            alloc.update_sizes(j)
            size2 = alloc.nodesize[j]
            if size != size2:
                print x.serialize()
                raise Exception("node sizes don't work", (j, size, size2))
    for i in range(6000):
        if l and random.randint(0, 1):
            x.delete(l[0])
            del l[0]
        else:
            r = random.randint(0, 999999)
            l.append(r)
            x.add(r)
        if tuple(x.traverser()) != tuple(sorted(l)):
            raise Exception("problems")
        checknodesizes()
    return x

def speedtest():
    import random
    def rnf(): return node(random.randint(0, 999), random.randint(0, 999))
    x = btree()
    l = []
    for i in range(60):
        r = rnf()
        l.append(r)
        x.add(r)
    random.shuffle(l)
    for i in range(2**16):
        if l and random.random() > 0.51:
            x.delete(l[0])
            del l[0]
        else:
            r = rnf()
            l.append(r)
            x.add(r)
    return x

def unit():
    import unittest
    unittest.TextTestRunner(verbosity=3).run(
        unittest.TestLoader().loadTestsFromTestCase(TestAddDelete))

def profile():
    import cProfile
    cProfile.run("speedtest()")

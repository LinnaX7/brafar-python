import zss
from zss.simple_tree import Node
from basic_framework.bidirectional_refactoring.cs_node import CSNode



def post_order(tlist: list, llist: list, t_node: CSNode):
    ret = 1
    llc_num = 0
    nlc_num = 0
    for i in range(len(t_node.children)):
        if i == 0:
            llc_num = post_order(tlist, llist, t_node.children[i])
        else:
            nlc_num = post_order(tlist, llist, t_node.children[i]) + nlc_num

    ret = ret + llc_num + nlc_num
    tlist.append(t_node)
    now_t = len(tlist) - 1

    if len(t_node.children) == 0:
        llist.append(now_t) # leaf
    else:
        now_t = now_t - nlc_num - 1
        llist.append(llist[now_t])
    return ret


def init_node(cs_node: CSNode):
    label = str(cs_node.cs_type)
    if len(cs_node.children) == 0:
        return Node(label)
    children = []
    for child in cs_node.children:
        children.append(init_node(child))
    return Node(label, children)


class Distance:
    def __init__(self, node1, node2):
        self.Node1 = node1
        self.Node2 = node2
        self.dist, self.operations = zss.simple_distance(self.Node1, self.Node2, return_operations=True)
        # print(self.dist)
        # print(self.operations)

    def get_do(self):
        return self.dist, self.operations

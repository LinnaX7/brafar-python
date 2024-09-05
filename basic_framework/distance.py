import ast

import numpy
from fastcache import clru_cache
from zss import simple_distance
import zss
from zss.simple_tree import Node

from basic_framework.bidirectional_refactoring.cs_node import CSNode
from basic_framework.program_partition.program_builder import get_code
from basic_framework.program_partition.cfs import get_func_map
from basic_framework.program_partition.statement import get_token_list
from basic_framework.program_partition.utils import regularize

def zss_ast_visit(ast_node, parent_zss_node):
    zss_label = str_node(ast_node)
    if zss_label == "":
        for field, value in ast.iter_fields(ast_node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        zss_ast_visit(item, parent_zss_node)
            elif isinstance(value, ast.AST):
                zss_ast_visit(value, parent_zss_node)
    else:
        zss_node = Node(zss_label)
        for field, value in ast.iter_fields(ast_node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        zss_ast_visit(item, zss_node)
            elif isinstance(value, ast.AST):
                zss_ast_visit(value, zss_node)
        parent_zss_node.addkid(zss_node)


def str_node(node):
    return acc_str_node(node)

# accurate label approach
def acc_str_node(node):
    if hasattr(node, "id"):
        return node.id
    elif hasattr(node, "name"):
        return node.name
    elif hasattr(node, "arg"):
        return node.arg
    elif hasattr(node, "n"):
        return str(node.n)
    elif hasattr(node, "s"):
        return "\'" + node.s + "\'"
    else:
        if node.__class__.__name__ in ["Module", "Load", "Store"]:
            return ""
        else:
            return node.__class__.__name__


def zss_node_cnt(zss_node):
    s = 1
    for child_zss_node in zss_node.children:
        s += zss_node_cnt(child_zss_node)
    return s


def label_weight(l1, l2):
    if l1 == l2:
        return 0
    else:
        return 1


def get_zss_root_node(code):
    root_node = ast.parse(code)
    root_zss_node = Node("root")
    zss_ast_visit(root_node, root_zss_node)
    return root_zss_node


def zss_func_ast_size(code):
    root_node = ast.parse(code)
    root_zss_node = Node("root")
    zss_ast_visit(root_node, root_zss_node)
    return zss_node_cnt(root_zss_node)


def zss_code_ast_edit(code_a, code_b):
    root_node_a = ast.parse(code_a)
    root_zss_node_a = Node("root")
    zss_ast_visit(root_node_a, root_zss_node_a)

    root_node_b = ast.parse(code_b)
    root_zss_node_b = Node("root")
    zss_ast_visit(root_node_b, root_zss_node_b)

    cost, ops = simple_distance(root_zss_node_a, root_zss_node_b, label_dist=label_weight, return_operations=True)
    print(ops)
    return cost

@clru_cache(maxsize=1024)
def smt_lev_multi_func_code_distance(code_a, code_b, limit):
    code_a = regularize(code_a)
    code_b = regularize(code_b)
    token_list_a = get_token_list(code_a)
    token_list_b = get_token_list(code_b)
    return smt_lev_tl_dist(token_list_a, token_list_b, limit)


def smt_lev_tl_dist(token_list_a, token_list_b, limit):
    size_x = len(token_list_a) + 1
    size_y = len(token_list_b) + 1
    matrix = numpy.zeros((size_x, size_y))
    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if token_list_a[x - 1].string == token_list_b[y - 1].string:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1],
                    matrix[x, y - 1] + 1
                )
            else:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1] + 1,
                    matrix[x, y - 1] + 1
                )
        if all(matrix[x, y] > limit for y in range(size_y)):
            return limit + 1
    return matrix[size_x - 1, size_y - 1]




@clru_cache(maxsize=1024)
def multi_func_code_distance(code_a, code_b, ted_func):
    func_map_a = get_func_map(code_a)
    func_map_b = get_func_map(code_b)

    func_name_set = set(func_map_a.keys()).union(set(func_map_b.keys()))

    sum_d = 0
    for func_name in func_name_set:
        func_code_a = ""
        if func_name in func_map_a.keys():
            func_code_a = func_map_a[func_name]

        func_code_b = ""
        if func_name in func_map_b.keys():
            func_code_b = func_map_b[func_name]
        sum_d += ted_func(func_code_a, func_code_b)
    return sum_d


def lev_multi_func_code_distance(code_a, code_b):
    code_a = regularize(code_a)
    code_b = regularize(code_b)
    return multi_func_code_distance(code_a, code_b, lev_code_distance)


def lev_code_distance(func_code_a, func_code_b):
    token_list_a = get_token_list(func_code_a)
    token_list_b = get_token_list(func_code_b)
    return lev_tl_dist(token_list_a, token_list_b)


def lev_tl_dist(token_list_a, token_list_b):
    size_x = len(token_list_a) + 1
    size_y = len(token_list_b) + 1
    matrix = numpy.zeros((size_x, size_y))
    for x in range(size_x):
        matrix [x, 0] = x
    for y in range(size_y):
        matrix [0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if token_list_a[x-1].string == token_list_b[y-1].string:
                matrix[x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix[x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    return matrix[size_x - 1, size_y - 1]


class ProgramTree(ast.NodeVisitor):
    def __init__(self, p_path):
        self.__p_path = p_path
        self.__p_code = get_code(self.__p_path)
        self.__p_node = ast.parse(self.__p_code)
        self.__methods = {}
        self.__ast_size = 0
        self.visit(self.__p_node)

    def get_p_code(self):
        return self.__p_code

    def get_ast_size(self):
        return self.__ast_size

    def visit_FunctionDef(self, node):
        self.__methods[node.name] = ast.unparse(node)
        self.__ast_size += zss_func_ast_size(self.__methods[node.name])
        return node

    def get_method_by_name(self, name):
        return self.__methods.get(name)

    def calculate_distance_func(self, func_name, func_code):
        return zss_code_ast_edit(self.__methods.get(func_name), func_code)

    def get_closest_func(self, func_name, func_fnames):
        code = ""
        mini_cost = 10000000
        min_f_name = ""
        i = 0
        for func_code, f_name in func_fnames:
            cur_cost = self.calculate_distance_func(func_name, func_code)
            if cur_cost < mini_cost:
                code = func_code
                mini_cost = cur_cost
                min_f_name = f_name
            i += 1
        return code, min_f_name



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
        print(self.dist)
        print(self.operations)

    def get_do(self):
        return self.dist, self.operations

def syntax_check(code):
    try:
        compile(code, "<string>", "exec")
        return True
    except:
        return False

if __name__ == '__main__':
    code1 = get_code("test1.py")
    node = ast.parse(code1)
    syntax_check(code1)
    code2 = get_code("test2.py")
    # code1 = "return len(seq)"
    # code2 = ""
    print(zss_code_ast_edit(code1,code2))
    print(zss_func_ast_size(code1))

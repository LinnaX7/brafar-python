import ast
from _ast import FunctionDef, For, If, While
from enum import Enum


class CSType(Enum):
    IF_STMT = 1
    FOR_STMT = 2
    WHILE_STMT = 3
    BREAK_STMT = 4
    BASIC_BLOCK = 5
    RETURN_STMT = 6
    CONTINUE_STMT = 7
    ELSE_BRANCH = 8
    METHOD_DECLARATION = 9
    THEN_BRANCH = 10


def get_cs_type(st):
    cs_type = -1
    if type(st) == ast.If:
        cs_type = CSType.IF_STMT
    elif type(st) == ast.For:
        cs_type = CSType.FOR_STMT
    elif type(st) == ast.While:
        cs_type = CSType.WHILE_STMT
    elif type(st) == ast.Break:
        cs_type = CSType.BREAK_STMT
    elif type(st) == ast.Continue:
        cs_type = CSType.CONTINUE_STMT
    elif type(st) == ast.Return:
        cs_type = CSType.RETURN_STMT
    return cs_type


class CSNode(ast.NodeVisitor):
    def __init__(self, node, height, cs_type, parent, t_index):
        self.node = node
        self.height = height
        self.cs_type = cs_type
        self.parent = parent
        self.children = []
        self.t_index = t_index
        self.ancestor = None
        self.ancestorFW = None
        self.is_new = False
        self.has_d_be_matched = False
        self.init_ancestor()
        self.init_ancestorFW()

    def set_has_d_be_matched(self):
        self.has_d_be_matched = True

    def get_has_d_be_matched(self):
        return self.has_d_be_matched

    def get_parent(self):
        return self.parent

    def is_branch(self):
        if self.cs_type == CSType.ELSE_BRANCH or self.cs_type == CSType.THEN_BRANCH:
            return True
        else:
            return False

    def is_branch_c(self):
        if self.parent is None:
            return False
        elif self.parent.cs_type == CSType.ELSE_BRANCH or self.parent.cs_type == CSType.THEN_BRANCH:
            return True
        else:
            return False

    def init_ancestor(self):
        if self.parent is None:
            return
        self.ancestor = []
        self.ancestor.append(self.parent)
        if self.parent.ancestor is not None:
            self.ancestor.extend(self.parent.ancestor)

    def init_ancestorFW(self):
        if self.parent is None:
            return
        if self.parent.cs_type == CSType.FOR_STMT or self.parent.cs_type == CSType.WHILE_STMT:
            self.ancestorFW = []
            self.ancestorFW.append(self.parent)
        if self.parent.ancestorFW is not None:
            if self.ancestorFW is None:
                self.ancestorFW = []
            self.ancestorFW.extend(self.parent.ancestorFW)

    def set_new(self, is_new):
        self.is_new = is_new

    def visit_For(self, node: For):
        i = 0
        for st in node.body:
            cs_type = get_cs_type(st)
            if cs_type != -1:
                m = CSNode(st, self.height + 1, cs_type, self, i)
                m.add_children()
            i += 1
        self.parent.children.append(self)

    def visit_While(self, node: While):
        i = 0
        for st in node.body:
            cs_type = get_cs_type(st)
            if cs_type != -1:
                m = CSNode(st, self.height + 1, cs_type, self, i)
                m.add_children()
            i += 1
        self.parent.children.append(self)

    def visit_FunctionDef(self, node: FunctionDef):
        i = 0
        for st in node.body:
            cs_type = get_cs_type(st)
            if cs_type != -1:
                m = CSNode(st, self.height + 1, cs_type, self, i)
                m.add_children()
            i += 1

    def visit_If(self, node: If):
        self.insert_If_branch(node, CSType.THEN_BRANCH, node.body)
        if len(node.orelse) != 0:
            self.insert_If_branch(node, CSType.ELSE_BRANCH, node.orelse)
        self.parent.children.append(self)

    def insert_If_branch(self, node, cs_type, st_list):
        branch_node: CSNode = CSNode(node, self.height+1, cs_type, self, self.t_index)
        i = 0
        for st in st_list:
            cs_type = get_cs_type(st)
            if cs_type != -1:
                m = CSNode(st, self.height + 2, cs_type, branch_node, i)
                m.add_children()
            i += 1
        self.children.append(branch_node)

    def update_children_height(self):
        for child in self.children:
            child.height = self.height + 1
            child.update_children_height()

    def add_children(self):
        if self.cs_type == CSType.METHOD_DECLARATION:
            self.visit(self.node)
        elif self.cs_type == CSType.FOR_STMT:
            self.visit(self.node)
        elif self.cs_type == CSType.WHILE_STMT:
            self.visit(self.node)
        elif self.cs_type == CSType.IF_STMT:
            self.visit_If(self.node)

    def insert_else_node(self, index):
        self.children[index - 1].node.orelse.append(ast.Pass)
        # print(ast.dump(self.children[index - 1].node))
        # self.children[index - 1].node.orelse.append(ast.parse("a = 1+1").body[0])
        # print(ast.dump(self.children[index - 1].node))
        else_s = CSNode(self.children[index-1].node, self.height+1, CSType.ELSE_BRANCH,
                        self, self.children[index-1].t_index)
        self.children.insert(index, else_s)
        return else_s

    def remove_node(self, index):
        # if self.children[index].cs_type != CSType.ELSE_BRANCH:
        if self.cs_type == CSType.ELSE_BRANCH:
            self.node.orelse.pop(self.children[index].t_index)
            if len(self.node.orelse) == 0:
                self.node.orelse.append(ast.Pass)
        else:
            self.node.body.pop(self.children[index].t_index)
        self.children.pop(index)
        i = index
        while i < len(self.children):
            self.children[i].t_index -= 1
            i += 1

    def remove_cs_nodes(self, begin, end, t_begin):
        r_nodes = []
        r_cs_nodes = []
        c = self.children[end].t_index - t_begin + 1
        for i in range(t_begin, self.children[end].t_index+1):
            if self.cs_type == CSType.ELSE_BRANCH:
                r_nodes.append(self.node.orelse.pop(t_begin))
                if len(self.node.orelse) == 0:
                    self.node.orelse.append(ast.Pass)
            else:
                r_nodes.append(self.node.body.pop(t_begin))
        # t_begin = self.children[begin].t_index
        for i in range(begin, end+1):
            self.children[begin].t_index = self.children[begin].t_index - t_begin
            r_cs_nodes.append(self.children.pop(begin))
        i = begin
        while i < len(self.children):
            self.children[i].t_index -= c
            # self.children[i].t_index += 1
            i += 1
        return r_nodes, r_cs_nodes

    def insert_cs_node(self, index, o_node):
        if len(self.children) == 0:
            tree_in = 0
        elif len(self.children) <= index:
            tree_in = self.children[-1].t_index + 1
        else:
            tree_in = self.children[index].t_index
        o_node.t_index = tree_in
        o_node.height = self.height+1
        o_node.update_children_height()
        o_node.parent = self
        # o_node.init_ancestorFW()
        if o_node.cs_type != CSType.ELSE_BRANCH:
            if self.cs_type == CSType.ELSE_BRANCH:
                self.node.orelse.insert(tree_in, o_node.node)
            else:
                self.node.body.insert(tree_in, o_node.node)
        self.children.insert(index, o_node)
        i = index + 1
        while i < len(self.children):
            self.children[i].t_index += 1
            i += 1

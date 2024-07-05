import ast
import time
from enum import Enum
from basic_framework.bidirectional_refactoring.mapping import Mapping
from basic_framework.bidirectional_refactoring.cs_node import CSNode, CSType
from basic_framework.bidirectional_refactoring.refactoring import Refactoring, BranchChanging, ConditionChanging


class ActionType(Enum):
    INSERT = 1
    DELETE = 2
    MOVE = 3


class Action(ast.NodeTransformer):
    def __init__(self, a_type: ActionType):
        self.type = a_type


class Delete(Action):
    def __init__(self, a_type: ActionType, cs_node: CSNode):
        super().__init__(a_type)
        self.node = cs_node.node


def insert_cs_node(parent: CSNode, node: CSNode, src_to_dst, dst_to_src):
    # print("begin insert", node.cs_type)
    index = node.parent.children.index(node)
    if index != 0:
        l_node = dst_to_src[node.parent.children[index-1]]
        while l_node.parent is not parent:
            l_node = l_node.parent
        index = parent.children.index(l_node) + 1
    if len(parent.children) == 0:
        tree_in = 0
        index = 0
    elif len(parent.children) <= index:
        tree_in = parent.children[-1].t_index + 1
        index = len(parent.children)
    else:
        while index < len(parent.children) and not src_to_dst.keys().__contains__(parent.children[index]) and not parent.children[index].get_has_d_be_matched():
            index += 1
        if index == len(parent.children):
            tree_in = parent.children[-1].t_index + 1
        else:
            t1 = -1
            if index >= 1:
                t1 = parent.children[index-1].t_index
            t2 = node.t_index
            t3 = parent.children[index].t_index
            if t1 < t2 < t3:
                tree_in = t2
            else:
                tree_in = t3

    ins = Insert(ActionType.INSERT, tree_in, parent.node, node.cs_type, node.parent.cs_type)
    new_node = CSNode(ins.new_s, parent.height + 1, node.cs_type, parent, tree_in)
    new_node.set_new(True)
    parent.children.insert(index, new_node)
    i = index + 1
    while i < len(parent.children):
        parent.children[i].t_index += 1
        i += 1
    # print(ast.unparse(parent.node))
    src_to_dst[new_node] = node
    dst_to_src[node] = new_node
    # print(str.format("Insert {0} {1}", node.cs_type, parent.height))
    return new_node


def insert_branch(if_node: CSNode, node: CSNode, src_to_dst, dst_to_src):
    if node.cs_type == CSType.THEN_BRANCH:
        then_s = CSNode(if_node.node, if_node.height + 1, CSType.THEN_BRANCH,
                        if_node, if_node.t_index)
        then_s.set_new(True)
        if_node.children.append(then_s)
        src_to_dst[then_s] = node
        dst_to_src[node] = then_s
        # print("Inset Then Branch", if_node.height)
        return if_node.children[0]
    elif node.cs_type == CSType.ELSE_BRANCH:
        if_node.node.orelse.append(ast.Pass())
        else_s = CSNode(if_node.node, if_node.height + 1, CSType.ELSE_BRANCH,
                        if_node, if_node.t_index)
        else_s.set_new(is_new=True)
        if_node.children.append(else_s)
        src_to_dst[else_s] = node
        dst_to_src[node] = else_s
        # print("Insert Else Branch", if_node.height)
        return else_s


def condition_change(node):
    if node.cs_type == CSType.ELSE_BRANCH and node.parent.is_new is True:
        node.parent.node = ConditionChanging(node.parent.node).visit(node.parent.node)
        node.parent.is_new = False


def condition_change_anc(node):
    condition_change(node)
    node = node.parent
    for anc in node.ancestor:
        condition_change(anc)


def move_cs_nodes(src_nodes, branch_node):
    # if branch_node.cs_type == CSType.ELSE_BRANCH and branch_node.parent.is_new is True:
    #     branch_node.parent.node = ConditionChanging(branch_node.parent.node).visit(branch_node.parent.node)
    condition_change_anc(branch_node)
    child_begin = src_nodes[0]
    child_end = src_nodes[-1]
    child_parent = child_begin.parent
    while child_end.parent != child_parent:
        child_end = child_end.parent
    temp_branch_node = branch_node
    while temp_branch_node.parent.parent != child_parent:
        temp_branch_node = temp_branch_node.parent
    r_nodes, r_cs_nodes = child_parent.remove_cs_nodes(
        child_parent.children.index(child_begin), child_parent.children.index(child_end), temp_branch_node.t_index+1)
    branch_node.children = r_cs_nodes
    if len(r_cs_nodes) != 0:
        for r_cs_node in r_cs_nodes:
            r_cs_node.parent = branch_node
            r_cs_node.height = branch_node.height - 1
            r_cs_node.update_children_height()
        if branch_node.cs_type == CSType.THEN_BRANCH:
            branch_node.node.body = r_nodes
        elif branch_node.cs_type == CSType.ELSE_BRANCH:
            branch_node.node.orelse = r_nodes


class Insert(Action):
    def __init__(self, a_type: ActionType, index, p_node, cs_type: CSType, p_type):
        super().__init__(a_type)
        self.index = index
        self.p_node = p_node
        self.new_s = None
        self.cs_type = cs_type
        self.p_type = p_type
        p_node = self.visit(p_node)

    def visit(self, node):
        if node is self.p_node:
            new_s = None
            if self.cs_type == CSType.IF_STMT:
                new_s = ast.parse("if True:"
                                  "  pass")
            elif self.cs_type == CSType.FOR_STMT:
                new_s = ast.parse("for i in range(0):"
                                  "  pass")
            elif self.cs_type == CSType.WHILE_STMT:
                new_s = ast.parse("while False:"
                                  "  pass")
            # print(ast.dump(if_s))
            if self.p_type == CSType.ELSE_BRANCH:
                if len(node.orelse) == 1 and type(node.orelse[0]) == ast.Pass:
                    node.orelse.clear()
                node.orelse.insert(self.index, new_s.body[0])
            else:
                node.body.insert(self.index, new_s.body[0])
            self.new_s = new_s.body[0]
        return node


class Move(Action):
    def __init__(self, a_type: ActionType, src_node: CSNode, dst_node: CSNode, src_parent: CSNode):
        super().__init__(a_type)
        index = dst_node.parent.children.index(dst_node)
        in2 = src_node.parent.children.index(src_node)
        src_node.parent.remove_node(in2)
        src_parent.insert_cs_node(index, src_node)


def init_cs_node(m_node):
    cs_node = CSNode(m_node, 0, CSType.METHOD_DECLARATION, None, 0)
    cs_node.add_children()
    return cs_node


class EditScript:
    def __init__(self, m_node1, m_node2):
        s_time = time.time()
        self.actions = []
        self.flag = True
        self.__m_node1 = m_node1
        self.__m_node2 = m_node2
        # Refactoring(self.__m_node1)
        # Refactoring(self.__m_node2)
        self.__cs_node1 = init_cs_node(m_node1)
        self.__cs_node2 = init_cs_node(m_node2)
        self._mapping = Mapping(self.__cs_node1, self.__cs_node2)
        self.dst_edit = 0
        self.src_edit = 0
        self.guidance = []
        self.check_best_match()
        self.refactory_guide()
        self.__refactored_code1 = ast.unparse(self.__m_node1)
        self.__refactored_code2 = ast.unparse(self.__m_node2)
        e_time = time.time()
        self.br_time = float("%.4f" % (e_time - s_time))

    def get_br_time(self):
        return self.br_time

    def get_refactored_code1(self):
        return self.__refactored_code1

    def get_refactored_code2(self):
        return self.__refactored_code2

    def check_best_match(self):
        _if_nodes = []
        for src, dst in self._mapping.src_to_dst.items():
            if src.cs_type == CSType.THEN_BRANCH and dst.cs_type == CSType.ELSE_BRANCH:
                _if_nodes.append(dst.node)
                # print("change branch node of if[{0}]", src.height - 1)
                self.guidance.append(str.format("change branch node of if[{0}]", dst.height - 1))
                # self.src_edit += 1
            elif src.cs_type == CSType.ELSE_BRANCH and dst.cs_type == CSType.THEN_BRANCH:
                _if_nodes.append(dst.node)
                # print("change branch node of if[{0}]", src.height - 1)
                self.guidance.append(str.format("change branch node of if[{0}]", dst.height - 1))
                # self.src_edit += 1
        if len(_if_nodes) != 0:
            self.__m_node2 = BranchChanging(_if_nodes).visit(self.__m_node2)
            self.__cs_node2 = init_cs_node(self.__m_node2)
            # print(ast.unparse(b_m.cs_node.node))
            # print(ast.unparse(c_m.cs_node.node))
            self._mapping = Mapping(self.__cs_node1, self.__cs_node2)

        # print(ast.unparse(_mapping.src_nodes[0].node))
        # print(ast.unparse(_mapping.dst_nodes[0].node))

    def insert_nodes(self, src_nodes, src_to_dst, dst_to_src):
        edit_actions = 0
        for src_node in src_nodes:
            if src_to_dst.get(src_node) is None:
                if src_to_dst.get(src_node.parent) is not None:
                    if src_node.cs_type == CSType.IF_STMT or src_node.cs_type == CSType.FOR_STMT or \
                            src_node.cs_type == CSType.WHILE_STMT:
                        insert_cs_node(src_to_dst.get(src_node.parent), src_node, dst_to_src, src_to_dst)
                        edit_actions += 1
                        self.guidance.append(str.format("Insert {0} {1}", src_node.cs_type,
                                                        src_to_dst.get(src_node.parent).height+1))
                    elif src_node.cs_type == CSType.THEN_BRANCH or src_node.cs_type == CSType.ELSE_BRANCH:
                        new_node = insert_branch(src_to_dst.get(src_node.parent), src_node, dst_to_src, src_to_dst)
                        children = []
                        for child in src_node.children:
                            s_child = src_to_dst.get(child)
                            if s_child is not None:
                                children.append(s_child)
                        if len(children) != 0:
                            move_cs_nodes(children, new_node)
                        if src_node.cs_type == CSType.ELSE_BRANCH and not src_node.parent.is_new:
                            edit_actions += 1
                        self.guidance.append(str.format("Insert Branch of if_node {0}",
                                                        src_to_dst.get(src_node.parent).height))
                    else:
                        self.flag = False
                else:
                    self.flag = False
        return edit_actions

    def refactory_guide(self):
        self.dst_edit += self.insert_nodes(self._mapping.src_nodes, self._mapping.src_to_dst, self._mapping.dst_to_src)
        if not self.flag:
            return
        self.src_edit += self.insert_nodes(self._mapping.dst_nodes, self._mapping.dst_to_src, self._mapping.src_to_dst)


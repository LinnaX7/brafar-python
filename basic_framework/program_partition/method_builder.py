import ast
from _ast import If, For, While, Call
from typing import Any
from zss.simple_tree import Node

from basic_framework.bidirectional_refactoring.refactoring import InitialRefactor
from basic_framework.program_partition.variable_builder import VariableBuilder
from basic_framework.bidirectional_refactoring.cs_node import CSNode, CSType
from basic_framework.program_partition.block_builder import BlockBuilder, BlockNode, BlockType, is_jump

class MethodBuilder(ast.NodeVisitor):
    def __init__(self, m_node, p_program):
        self.cs_node = None
        self.f_name = p_program.get_f_name()
        self.b_funcs = p_program.get_b_funcs()
        self.m_name = m_node.name
        self.call_funcs = []
        self.cfs = ""
        self.struct_list = []
        self.struct = ""
        self.lines = 0
        self.m_node = m_node
        self.struct_node = None
        self.struct_temp = []
        self.method_code = ast.unparse(self.m_node)
        self.block_builder = None
        self.block_builder: BlockBuilder
        self.variable_builder = None
        self.meta_block_nodes = None
        self.contains_inner_func = False
        self.recursive = False
        InitialRefactor(self.m_node)

    def is_recursive(self):
        return self.recursive

    def is_containing_inner_func(self):
        return self.contains_inner_func

    def get_method_code(self):
        return self.method_code

    def init_(self):
        self.visit(self.m_node)
        self.cs_node = None
        self.init_cs_node()
        self.method_code = ast.unparse(self.m_node)
        self.block_builder = None
        self.block_builder: BlockBuilder
        self.variable_builder = None
        self.meta_block_nodes = None
        self.call_funcs.sort()
        # print(self.cfs)

    def get_m_node(self):
        return self.m_node

    def init_block_builder(self):
        self.block_builder = BlockBuilder(self.m_node)
        self.meta_block_nodes = self.block_builder.get_meta_blocks()

    def get_meta_block_nodes(self):
        return self.meta_block_nodes

    def init_variable_builder(self):
        self.variable_builder = VariableBuilder(self.m_node)
        self.set_variable_DU()

    def get_block_builder(self):
        return self.block_builder

    def get_cfs(self):
        return self.cfs

    def get_variable_builder(self):
        return self.variable_builder

    def set_block_variable_DU(self, block_index, block_node: BlockNode):
        for node in block_node.get_ast_nodes():
            if is_jump(node) != -1:
                continue
            for node in ast.walk(node):
                if isinstance(node, ast.Name):
                    self.variable_builder.set_variable_DU(node.id, block_index, block_node.get_meta_score())
                    if isinstance(node.ctx, ast.Store):
                        self.variable_builder.set_variable_Define(node.id, block_index)
                elif isinstance(node, ast.arg):
                    self.variable_builder.set_variable_DU(node.arg, block_index, block_node.get_meta_score())
        if block_node.get_jump_block() is not None:
            if block_node.get_jump_block().get_type() == BlockType.RETURN:
                for node in ast.walk(block_node.get_jump_block().get_ast_node()):
                    if isinstance(node, ast.Name):
                        self.variable_builder.set_variable_return_use(node.id, block_index,
                                                                      block_node.get_jump_block().get_meta_score())
                    elif isinstance(node, ast.arg):
                        self.variable_builder.set_variable_return_use(node.arg, block_index,
                                                                      block_node.get_jump_block().get_meta_score())

    def set_variable_DU(self):
        for i in range(len(self.meta_block_nodes)):
            self.set_block_variable_DU(i, self.meta_block_nodes[i])

    def init_cs_node(self):
        self.cs_node = CSNode(self.m_node, 0, CSType.METHOD_DECLARATION, None, 0)
        self.cs_node.add_children()

    def set_m_node(self, node):
        self.m_node = node
        self.init_cs_node()

    def visit_FunctionDef(self, node):
        # print('Function Name: %s' % node.name)
        if node.name != self.m_node.name:
            self.contains_inner_func = True
            return
        self.generic_visit(node)
        children = []
        children.extend(self.struct_temp)
        self.struct_temp.clear()
        self.struct_node = Node("Sig", children)
        self.lines = node.end_lineno-node.lineno + 1

    def get_children_node(self, begin):
        children = []
        if len(self.struct_temp) > 0:
            children.extend(self.struct_temp[begin:])
            if begin == 0:
                self.struct_temp.clear()
            else:
                self.struct_temp = self.struct_temp[0:begin]
        return children

    def visit_For(self, node: For):
        if self.cfs != "":
            self.cfs += ","
        self.cfs += "For_start"
        self.struct_list.append("for")
        begin = len(self.struct_temp)
        self.generic_visit(node)
        children = self.get_children_node(begin)
        self.struct_temp.append(Node("For", children))
        self.cfs += ",For_end"

    def visit_While(self, node: While):
        if self.cfs != "":
            self.cfs += ","
        self.cfs += "While_start"
        self.struct_list.append("while")
        begin = len(self.struct_temp)
        self.generic_visit(node)
        children = self.get_children_node(begin)
        self.struct_temp.append(Node("While", children))
        self.cfs += ",While_end"

    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.b_funcs and not self.call_funcs.__contains__(func_name):
                if func_name == self.m_name:
                    self.recursive = True
                else:
                    self.call_funcs.append(func_name)
        self.generic_visit(node)

    def get_call_funcs(self):
        return self.call_funcs

    def visit_If(self, node: If) -> Any:
        if self.cfs != "":
            self.cfs += ","
        self.cfs += "IF_start"
        self.struct_list.append("if")
        # self.visit(node.test)
        begin1 = len(self.struct_temp)
        if len(node.body) != 0:
            for st in node.body:
                self.visit(st)
        self.cfs += ",IF_end"
        if len(node.orelse) != 0:
            self.cfs += ",Else_start"
            self.struct_list.append("else")
            begin = len(self.struct_temp)
            for st in node.orelse:
                self.visit(st)
            children2 = self.get_children_node(begin)
            # self.struct_temp.append(Node("If", children1))
            self.struct_temp.append(Node("Else", children2))
            self.cfs += ",Else_end"
        children1 = self.get_children_node(begin1)
        self.struct_temp.append(Node("If", children1))

    # def visit_Return(self, node: Return) -> Any:
    #     if self.cfs != "":
    #         self.cfs += ","
    #     self.cfs += "Return"
    #     self.struct_list.append("return")
    #     return node
    #
    # def visit_Break(self, node: Break) -> Any:
    #     if self.cfs != "":
    #         self.cfs += ","
    #     self.cfs += "Break"
    #     self.struct_list.append("break")
    #     return node
    #
    # def visit_Continue(self, node: Continue) -> Any:
    #     if self.cfs != "":
    #         self.cfs += ","
    #     self.cfs += "Continue"
    #     self.struct_list.append("continue")
    #     return node

    def cpr_struct_list(self):
        for struct in self.struct_list:
            if struct == "for":
                self.struct += "f"
            elif struct == "while":
                self.struct += "w"
            elif struct == "if":
                self.struct += "i"
            elif struct == "else":
                self.struct += "e"
            elif struct == "return":
                self.struct += "r"
            elif struct == "break":
                self.struct += "b"
            elif struct == "continue":
                self.struct += "c"
        return self.struct

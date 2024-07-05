from _ast import For, While, If
from typing import Any
import ast

from basic_framework.program_partition.block_builder import get_block_type, is_jump



class Hole(ast.NodeVisitor):
    def __init__(self, m_node):
        # self.__block_builder = block_builder
        # self.__root_block: BlockNode = block_builder.get_root_block()
        # self.__original_code = ast.unparse(block_builder.get_m_node())
        self.__original_code = ast.unparse(m_node)
        self.__m_node = ast.parse(self.__original_code)
        self.__basic_block_index = -1
        self.visit(self.__m_node)
        self.__var_hist_instrumented_code = ast.unparse(self.__m_node)

    def get_m_node(self):
        return self.__m_node.body[0]

    def get_instrument_node(self):
        block_index_str = "block" + str(self.__basic_block_index)
        __instrument_code = "print(" + "\"" + block_index_str + ":\", locals())"
        __instrument_node = ast.parse(__instrument_code).body[0]
        return __instrument_node

    def get_instrumented_code(self):
        return self.__var_hist_instrumented_code

    def visit_body(self, body):
        instrumented_body = []
        pre_st = None
        for st in body:
            block_type = get_block_type(st)
            if pre_st is None or get_block_type(pre_st) != -1:
                self.__basic_block_index += 1
                instrumented_body.append(self.get_instrument_node())
                pre_st = st
            elif block_type == -1:
                pre_st = st
            if block_type != -1:
                instrumented_body.append(self.get_instrument_node())
                self.visit(st)
                pre_st = st
            if is_jump(st) != -1:
                instrumented_body.append(self.get_instrument_node())
            instrumented_body.append(st)
        if pre_st is None or get_block_type(pre_st) != -1:
            self.__basic_block_index += 1
            instrumented_body.append(self.get_instrument_node())
        if pre_st is None or is_jump(pre_st) == -1:
            instrumented_body.append(self.get_instrument_node())
        return instrumented_body

    def visit_FunctionDef(self, node):
        node.body = self.visit_body(node.body)
        return node

    def visit_For(self, node: For) -> Any:
        self.__basic_block_index += 1
        node.body = self.visit_body(node.body)

    def visit_While(self, node: While) -> Any:
        self.__basic_block_index += 1
        node.body = self.visit_body(node.body)

    def visit_If(self, node: If) -> Any:
        self.__basic_block_index += 1
        node.body = self.visit_body(node.body)
        if len(node.orelse) != 0:
            node.orelse = self.visit_body(node.orelse)






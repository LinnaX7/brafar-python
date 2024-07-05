import ast

from basic_framework.program_partition.block_builder import BlockNode, BlockType
from basic_framework.program_partition.method_builder import MethodBuilder
from basic_framework.program_partition.variable_builder import Variable


def check_variable_type(var1, var2):
    if var1.get_type() is None:
        return True
    if var2.get_type() is None:
        return True
    if var1.get_type() == "List" or var2.get_type() == "List":
        if var1.get_type() != var2.get_type():
            return False
    return True


class Aligner:
    def __init__(self, method_builder1: MethodBuilder, method_builder2: MethodBuilder):
        method_builder1.init_block_builder()
        method_builder2.init_block_builder()
        self.__block_builder1 = method_builder1.get_block_builder()
        self.__block_builder2 = method_builder2.get_block_builder()
        method_builder1.init_variable_builder()
        method_builder2.init_variable_builder()
        # print(ast.dump(method_builder1.m_node))
        self.__variable_builder1 = method_builder1.get_variable_builder()
        self.__variable_builder2 = method_builder2.get_variable_builder()
        self.__meta_blocks1 = self.__block_builder1.get_meta_blocks()
        self.__block_map = {}
        self.__variable_map_12 = {}
        self.__variable_map_21 = {}
        self.__unmatched_variables1 = []
        self.__unmatched_variables2 = []
        self.block_alignment()
        self.variable_alignment()

    def get_variable_builder(self):
        return self.__variable_builder1

    def add_variable_map(self, var1, var2):
        self.__variable_map_12[var1] = var2
        self.__variable_map_21[var2] = var1

    def get_block_map(self):
        return self.__block_map

    def get_variable_map_12(self):
        return self.__variable_map_12

    def get_variable_map_21(self):
        return self.__variable_map_21

    def get_c_variable_def_index(self, var_name):
        if self.__variable_builder2.get_variable_by_name(var_name) is None:
            return None
        return self.__variable_builder2.get_variable_by_name(var_name).get_def()

    def block_alignment(self):
        self.block_alignment_core(self.__block_builder1.get_root_block(), self.__block_builder2.get_root_block())

    def block_alignment_core(self, block1: BlockNode, block2: BlockNode):
        self.__block_map[block1] = block2
        children_len = len(block1.get_children())
        if children_len != 0:
            for i in range(children_len):
                block1_c = block1.get_children()[i]
                block2_c = block2.get_children()[i]
                self.block_alignment_core(block1_c, block2_c)

    def align_while_cond(self):
        for block_node in self.__meta_blocks1:
            if block_node.get_type() == BlockType.WHILE_COND:
                vars1 = []
                vars2 = []
                for node in ast.walk(block_node.get_ast_nodes()[0]):
                    if isinstance(node, ast.Name):
                        if self.__variable_builder1.get_variable_by_name(node.id) is not None:
                            if not vars1.__contains__(self.__variable_builder1.get_variable_by_name(node.id)):
                                if self.__unmatched_variables1.__contains__(self.__variable_builder1.get_variable_by_name(node.id)):
                                    vars1.append(self.__variable_builder1.get_variable_by_name(node.id))
                for node in ast.walk(self.__block_map.get(block_node).get_ast_nodes()[0]):
                    if isinstance(node, ast.Name):
                        if self.__variable_builder2.get_variable_by_name(node.id) is not None:
                            if not vars2.__contains__(self.__variable_builder2.get_variable_by_name(node.id)):
                                if self.__unmatched_variables2.__contains__(self.__variable_builder2.get_variable_by_name(node.id)):
                                    vars2.append(self.__variable_builder2.get_variable_by_name(node.id))
                for i in range(min(len(vars1), len(vars2))):
                    if self.__unmatched_variables1.__contains__(vars1[i]) and self.__unmatched_variables2.__contains__(vars2[i]):
                        self.__variable_map_12[vars1[i].get_name()] = vars2[i].get_name()
                        self.__variable_map_21[vars2[i].get_name()] = vars1[i].get_name()
                        self.__unmatched_variables1.remove(vars1[i])
                        self.__unmatched_variables2.remove(vars2[i])

    def align_for_targets(self):
        for block_node in self.__meta_blocks1:
            if block_node.get_type() == BlockType.FOREACH_ITER:
                vars1 = []
                vars2 = []
                for node in ast.walk(block_node.get_ast_nodes()[0]):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                        if self.__variable_builder1.get_variable_by_name(node.id) is not None:
                            vars1.append(self.__variable_builder1.get_variable_by_name(node.id))
                for node in ast.walk(self.__block_map.get(block_node).get_ast_nodes()[0]):
                    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                        if self.__variable_builder2.get_variable_by_name(node.id) is not None:
                            vars2.append(self.__variable_builder2.get_variable_by_name(node.id))
                for i in range(min(len(vars1), len(vars2))):
                    if self.__unmatched_variables1.__contains__(vars1[i]) and self.__unmatched_variables2.__contains__(vars2[i]):
                        self.__variable_map_12[vars1[i].get_name()] = vars2[i].get_name()
                        self.__variable_map_21[vars2[i].get_name()] = vars1[i].get_name()
                        self.__unmatched_variables1.remove(vars1[i])
                        self.__unmatched_variables2.remove(vars2[i])
                vars1 = []
                vars2 = []
                for node in ast.walk(block_node.get_ast_nodes()[1]):
                    if isinstance(node, ast.Name):
                        if self.__variable_builder1.get_variable_by_name(node.id) is not None:
                            vars1.append(self.__variable_builder1.get_variable_by_name(node.id))
                for node in ast.walk(self.__block_map.get(block_node).get_ast_nodes()[0]):
                    if isinstance(node, ast.Name):
                        if self.__variable_builder2.get_variable_by_name(node.id) is not None:
                            vars2.append(self.__variable_builder2.get_variable_by_name(node.id))
                for i in range(min(len(vars1), len(vars2))):
                    if self.__unmatched_variables1.__contains__(vars1[i]) and self.__unmatched_variables2.__contains__(
                            vars2):
                        self.__variable_map_12[vars1[i].get_name()] = vars2[i].get_name()
                        self.__variable_map_21[vars2[i].get_name()] = vars1[i].get_name()
                        self.__unmatched_variables1.remove(vars1[i])
                        self.__unmatched_variables2.remove(vars2[i])

    def variable_alignment(self):
        self.__unmatched_variables1.extend(self.__variable_builder1.get_variable_list())
        self.__unmatched_variables2.extend(self.__variable_builder2.get_variable_list())
        params1 = self.__variable_builder1.get_param_list()
        params2 = self.__variable_builder2.get_param_list()
        for i in range(len(params1)):
            self.__variable_map_12[params1[i].get_name()] = params2[i].get_name()
            self.__variable_map_21[params2[i].get_name()] = params1[i].get_name()
            self.__unmatched_variables1.remove(params1[i])
            self.__unmatched_variables2.remove(params2[i])
        self.align_for_targets()
        self.align_while_cond()
        self.variable_alignment_EDUA()
        self.align_ret_variables()
        self.variable_alignment_by_name()

    def align_ret_variables(self):
        if len(self.__variable_builder1.get_ret_vars()) == 1 and len(self.__variable_builder2.get_ret_vars()) == 1:
            var1 = self.__variable_builder1.get_ret_vars()[0]
            var2 = self.__variable_builder2.get_ret_vars()[0]
            if self.__unmatched_variables1.__contains__(var1):
                if self.__unmatched_variables2.__contains__(var2):
                    self.__variable_map_12[var1.get_name()] = var2.get_name()
                    self.__variable_map_21[var2.get_name()] = var1.get_name()
                    self.__unmatched_variables1.remove(var1)
                    self.__unmatched_variables2.remove(var2)

    def variable_alignment_EDUA(self):
        for var1 in self.__unmatched_variables1:
            for var2 in self.__unmatched_variables2:
                if var1.get_uses() == var2.get_uses():
                    self.__variable_map_12[var1.get_name()] = var2.get_name()
                    self.__variable_map_21[var2.get_name()] = var1.get_name()
                    self.__unmatched_variables1.remove(var1)
                    self.__unmatched_variables2.remove(var2)
                    break
        if len(self.__unmatched_variables1) != 0:
            self.variable_alignment_EDUA_by_similarity(0.9)
        if len(self.__unmatched_variables1) != 0:
            self.variable_alignment_EDUA_by_similarity(0.8)
        if len(self.__unmatched_variables1) != 0:
            self.variable_alignment_EDUA_by_similarity(0.7)
        if len(self.__unmatched_variables1) != 0:
            self.variable_alignment_EDUA_by_similarity(0.6)
        if len(self.__unmatched_variables1) != 0:
            self.variable_alignment_EDUA_by_similarity(0.5)

    def variable_alignment_EDUA_by_similarity(self, bound):
        for var1 in self.__unmatched_variables1:
            max_sim = 0.0
            max_var = None
            for var2 in self.__unmatched_variables2:
                sim = self.calculate_similarity(var1, var2)
                if check_variable_type(var1, var2):
                    if sim > bound and sim > max_sim:
                        max_sim = sim
                        max_var = var2
            if max_var is not None:
                self.__variable_map_12[var1.get_name()] = max_var.get_name()
                self.__variable_map_21[max_var.get_name()] = var1.get_name()
                self.__unmatched_variables1.remove(var1)
                self.__unmatched_variables2.remove(max_var)

    def calculate_similarity(self, variable1: Variable, variable2: Variable):
        match_mark = 0
        for use in variable1.get_uses():
            if variable2.get_uses().__contains__(use):
                match_mark += self.__meta_blocks1[use].get_meta_score()
        if variable1.get_return_uses() is not None:
            for use in variable1.get_return_uses():
                if variable2.get_return_uses() is not None:
                    # if variable2.get_return_uses().__contains__(use):
                    match_mark += self.__meta_blocks1[use].get_jump_block().get_meta_score()
        return float(match_mark) / float(max(variable1.get_def_use_mark(), variable2.get_def_use_mark()))

    def variable_alignment_by_name(self):
        for var1 in self.__unmatched_variables1:
            for var2 in self.__unmatched_variables2:
                if var1.get_name() == var2.get_name():
                    self.__variable_map_12[var1.get_name()] = var2.get_name()
                    self.__variable_map_21[var2.get_name()] = var1.get_name()
                    self.__unmatched_variables1.remove(var1)
                    self.__unmatched_variables2.remove(var2)
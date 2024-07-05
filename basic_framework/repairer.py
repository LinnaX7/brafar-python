import ast
import os.path
import copy

from basic_framework.aligner import Aligner
from basic_framework.program_partition.block_builder import JumpNode


class Re:
    def __init__(self, benchmark_dir_path, question_name, sr_list, exp_time):
        self.__cur_question_name = question_name
        self.__ques_dir_path = os.path.join(benchmark_dir_path, self.__cur_question_name)
        self.__ans_dir_path = os.path.join(benchmark_dir_path, "base", self.__cur_question_name, "ans")
        self.__correct_code_dir_path = os.path.join(benchmark_dir_path, "base", self.__cur_question_name, "correct")
        self.__reference_code_path = os.path.join(benchmark_dir_path, self.__cur_question_name, "reference.py")
        self.__sr_list = sr_list
        self.__exp_time = exp_time


class Repairer:
    def __init__(self, block_node, method_aligner: Aligner):
        self.__cur_block = block_node
        self.__method_aligner = method_aligner
        self.__mapped_block = method_aligner.get_block_map()[self.__cur_block]
        self.__variable_map_21 = method_aligner.get_variable_map_21()
        self.__need_repair_back = False
        self.__begin_index = -1
        self.repair()

    def get_need_repair_back(self):
        return self.__need_repair_back

    def get_begin_index(self):
        return self.__begin_index

    def repair(self):
        repaired_ast_nodes = []
        for ast_node in self.__mapped_block.get_ast_nodes():
            new_ast_node = copy.deepcopy(ast_node)
            for node in ast.walk(new_ast_node):
                if isinstance(node, ast.Name):
                    if self.__variable_map_21.get(node.id) is not None:
                        node.id = self.__variable_map_21.get(node.id)
                    else:
                        if self.__method_aligner.get_c_variable_def_index(node.id) is not None:
                            # self.__need_repair_back = True
                            var1 = node.id
                            if self.__method_aligner.get_variable_builder().get_variable_by_name(node.id) is not None:
                                var1 = "__new__"+node.id
                            self.__method_aligner.add_variable_map(var1, node.id)
                            var_def_index = self.__method_aligner.get_c_variable_def_index(node.id)
                            if self.__begin_index == -1 or self.__begin_index > var_def_index:
                                self.__begin_index = var_def_index
                            node.id = self.__variable_map_21.get(node.id)
            repaired_ast_nodes.append(new_ast_node)
        self.__cur_block.set_ast_nodes(repaired_ast_nodes)
        if self.__mapped_block.get_jump_block() is not None:
            new_ast_node = copy.deepcopy(self.__mapped_block.get_jump_block().get_ast_node())
            for node in ast.walk(new_ast_node):
                if isinstance(node, ast.Name):
                    if self.__variable_map_21.get(node.id) is not None:
                        node.id = self.__variable_map_21.get(node.id)
                    else:
                        if self.__method_aligner.get_c_variable_def_index(node.id) is not None:
                            # self.__need_repair_back = True
                            var1 = node.id
                            if self.__method_aligner.get_variable_builder().get_variable_by_name(node.id) is not None:
                                var1 = "__new__" + node.id
                            self.__method_aligner.add_variable_map(var1, node.id)
                            var_def_index = self.__method_aligner.get_c_variable_def_index(node.id)
                            if self.__begin_index == -1 or self.__begin_index > var_def_index:
                                self.__begin_index = var_def_index
                            node.id = self.__variable_map_21.get(node.id)
            self.__cur_block.set_jump_block(JumpNode(self.__mapped_block.get_jump_block().get_type(), new_ast_node))
        else:
            self.__cur_block.set_jump_block(None)

import ast
import os.path
import random
import time

import numpy as np
import pandas as pd

from basic_framework.program_partition.block_builder import BlockType
from basic_framework.bidirectional_refactoring.edit_script import EditScript
from basic_framework.bidirectional_refactoring.refactoring import Recover
from basic_framework.distance import ProgramTree
from basic_framework.searcher import Searcher
from basic_framework.program_partition.program_builder import get_program, Reconstructor, get_code, syntax_check
from basic_framework.aligner import Aligner
from basic_framework.repairer import Repairer
from basic_framework.fault_locator import FaultLocator, TestResult


def get_file_list(p_dir_path, sample_rate):
    path_list = []
    for file_name in os.listdir(p_dir_path):
        if file_name.endswith(".DS_Store"):
            continue
        code_path = os.path.join(p_dir_path, file_name)
        path_list.append(code_path)
    random.shuffle(path_list)
    l = len(path_list)
    path_list = path_list[:int(sample_rate / 100 * l)]
    return path_list
            

def get_case_paths(dir_path, type_name):
    res = []
    for file_name in os.listdir(dir_path):
        curr_path = os.path.join(dir_path, file_name)
        if os.path.isfile(curr_path):
            if file_name.__contains__(type_name):
                res.append(curr_path)
    return res


class Brafar:
    def __init__(self, buggy_f, correct_f, func_name, ans_dir_path, _global):
        self._init_test_result = None
        self.__repaired_code = None
        self.__repair_result = False
        self.__has_fixed = None
        self.__aligner = None
        self.__MAX_REPAIR_COUNT = 20
        self.buggy_p = get_program(buggy_f)
        self.buggy_m = self.buggy_p.get_method(func_name)
        self.correct_p = get_program(correct_f)
        self.correct_m = self.correct_p.get_method(func_name)
        self.__test_case_inputs = sorted(get_case_paths(ans_dir_path, "input"))
        self.__test_case_outputs = sorted(get_case_paths(ans_dir_path, "output"))
        self.__global_path = _global
        self.__bidirectional_refactory = None
        self.__refactored_buggy_code = self.buggy_m.method_code
        self.__refactored_correct_code = self.correct_m.method_code
        self.init_test()
        self.br_time = 0.0
        if self.__repair_result:
            self.__repaired_code = ast.unparse(self.buggy_m.get_m_node())
            self.fl_repair_time = 0.0
            return
        self.bidirectional_refactoring()
        # print(buggy_f)
        # print(correct_f)
        self.__aligner = Aligner(self.buggy_m, self.correct_m)
        self.buggy_m.get_block_builder().update_m_node()
        self.__has_fixed = []
        self.__repair_result = False
        self.__repaired_code = None
        # self.block_by_block_repair()
        # self.buggy_m.get_block_builder().update_m_node()
        s_time = time.time()
        if self.correct_m.is_recursive():
            self.block_by_block_repair()
        else:
            self.repair_with_afl()
        e_time = time.time()
        self.fl_repair_time = float("%.4f" % (e_time - s_time))

    def bidirectional_refactoring(self):
        if self.buggy_m.get_cfs() == self.correct_m.get_cfs():
            self.__refactored_buggy_code = self.buggy_m.get_method_code()
            self.__refactored_correct_code = self.correct_m.get_method_code()
            self.br_time = 0.0
        else:
            self.__bidirectional_refactory = EditScript(self.buggy_m.m_node, self.correct_m.m_node)
            self.__refactored_buggy_code = self.__bidirectional_refactory.get_refactored_code1()
            self.__refactored_correct_code = self.__bidirectional_refactory.get_refactored_code2()
            self.br_time = self.__bidirectional_refactory.get_br_time()

    def get_br_time(self):
        return self.br_time

    def get_refactored_buggy_code(self):
        return self.__refactored_buggy_code

    def get_refactored_correct_code(self):
        return self.__refactored_correct_code

    def get_fl_repair_time(self):
        return self.fl_repair_time

    def init_test(self):
        reconstructed_p = Reconstructor(self.correct_p.get_p_node(), self.buggy_m.get_m_node())
        self._init_test_result = TestResult(ast.unparse(reconstructed_p.get_reconstructed_p_node()),
                                            self.__test_case_inputs, self.__test_case_outputs, self.__global_path)
        self.__repair_result = self._init_test_result.get_test_result()

    def block_by_block_repair(self):
        for block_node in self.buggy_m.get_meta_block_nodes():
            Repairer(block_node, self.__aligner)
        self.buggy_m.get_block_builder().update_m_node()
        reconstructed_p = Reconstructor(self.correct_p.get_p_node(), self.buggy_m.get_m_node())
        code = ast.unparse(reconstructed_p.get_reconstructed_p_node())
        # print("======================= Repair", repair_count, "============================")
        # print(code)
        test_result = TestResult(code, self.__test_case_inputs,
                                 self.__test_case_outputs, self.__global_path)
        # print("==================== End Repair =======================")
        # print("Repair Result:", test_result.get_test_result())
        self.__repair_result = test_result.get_test_result()
        if self.__bidirectional_refactory is not None:
            Recover(self.buggy_m.get_m_node())
        self.__repaired_code = ast.unparse(self.buggy_m.get_m_node())

    def get_repaired_code(self):
        return self.__repaired_code

    def block_by_block_repair_from_all(self, begin_in, end_in):
        need_repair_back = True
        back_begin_index = begin_in
        while back_begin_index >= 0 and need_repair_back:
            begin_in = back_begin_index
            need_repair_back = False
            back_begin_index = -1
            for i in range(begin_in, end_in):
                __repairer = Repairer(self.buggy_m.get_meta_block_nodes()[i], self.__aligner)
                if __repairer.get_need_repair_back():
                    need_repair_back = True
                    if back_begin_index == -1 or __repairer.get_begin_index() < back_begin_index:
                        back_begin_index = __repairer.get_begin_index()
            end_in = begin_in

    def block_by_block_repair_from(self, begin_in, end_in, trace: list):
        need_repair_back = True
        back_begin_index = begin_in
        while back_begin_index >= 0 and need_repair_back:
            begin_in = back_begin_index
            need_repair_back = False
            back_begin_index = -1
            for i in range(begin_in, end_in):
                if i==begin_in or trace.__contains__(i) or (self.buggy_m.get_meta_block_nodes()[i].get_type() != BlockType.BASIC_BLOCK and trace.__contains__(i+1)):
                    __repairer = Repairer(self.buggy_m.get_meta_block_nodes()[i], self.__aligner)
                    if __repairer.get_need_repair_back():
                        need_repair_back = True
                        if back_begin_index == -1 or __repairer.get_begin_index() < back_begin_index:
                            back_begin_index = __repairer.get_begin_index()
                    self.__has_fixed.append(i)
            end_in = begin_in

    def repair_block(self, cur_block, trace: list):
        __repairer = Repairer(cur_block, self.__aligner)
        if __repairer.get_need_repair_back():
            self.block_by_block_repair_from(__repairer.get_begin_index(), cur_block.get_meta_index(), trace)

    def get_repair_result(self):
        return self.__repair_result

    def repair_with_afl(self):
        test_result = self._init_test_result
        input_cases = test_result.get_failed_input_cases()
        output_cases = test_result.get_failed_output_cases()
        repair_count = 0
        while not test_result.get_test_result() and repair_count < self.__MAX_REPAIR_COUNT:
            fl = FaultLocator(self.buggy_m, self.correct_m, self.correct_p, input_cases[0],
                                            output_cases[0], self.__aligner, self.__has_fixed, self.__global_path)
            if fl.get_fault_block() is None:
                # print(False)
                self.block_by_block_repair()
                return
            if not self.__has_fixed.__contains__(fl.get_fault_block().get_meta_index()):
                if fl.get_test_result() is not None:
                    if fl.get_test_result().get_need_repair_all():
                        self.block_by_block_repair_from_all(fl.get_fault_block().get_meta_index(), len(self.buggy_m.get_meta_block_nodes()))
                    elif fl.get_test_result().get_need_b2b_repair():
                        self.block_by_block_repair_from(fl.get_fault_block().get_meta_index(), len(self.buggy_m.get_meta_block_nodes()), fl.get_correct_block_trace())
                    else:
                        self.repair_block(fl.get_fault_block(), fl.get_correct_block_trace())
                else:
                    self.repair_block(fl.get_fault_block(), fl.get_correct_block_trace())
                self.__has_fixed.append(fl.get_fault_block().get_meta_index())
            else:
                need_fixed_index = fl.get_fault_block().get_meta_index()-1
                flag = False
                while True:
                    if need_fixed_index < 0:
                        break
                    if not self.__has_fixed.__contains__(need_fixed_index):
                        self.repair_block(self.buggy_m.get_meta_block_nodes()[need_fixed_index],
                                          fl.get_correct_block_trace())
                        self.__has_fixed.append(need_fixed_index)
                        flag = True
                        break
                    need_fixed_index -= 1
                if not flag:
                    # print(False)
                    break
            self.buggy_m.get_block_builder().update_m_node()
            reconstructed_p = Reconstructor(self.correct_p.get_p_node(), self.buggy_m.get_m_node())
            code = ast.unparse(reconstructed_p.get_reconstructed_p_node())
            repair_count += 1
            # print("======================= Repair", repair_count, "============================")
            # print(code)
            test_result = TestResult(code, self.__test_case_inputs,
                                     self.__test_case_outputs, self.__global_path)
            input_cases = test_result.get_failed_input_cases()
            output_cases = test_result.get_failed_output_cases()
        # print("==================== End Repair =======================")
        # print("Repair Result:", test_result.get_test_result())
        self.__repair_result = test_result.get_test_result()
        if self.__bidirectional_refactory is not None:
            Recover(self.buggy_m.get_m_node())
        self.__repaired_code = ast.unparse(self.buggy_m.get_m_node())
        # if syntax_check(self.__repaired_code) is None:
        #     print(self.__repaired_code)
        # print(self.__repaired_code)

        # print(ast.unparse(reconstructed_p.get_reconstructed_p_node()))


    # def repair_with_afl(self):
    #     while not self.test_result:

def get_target_wrong_file(target_wrong_folder):
    base_name = os.path.basename(target_wrong_folder)
    for file in os.listdir(target_wrong_folder):
        if file.find(base_name) != -1:
            return os.path.join(target_wrong_folder, file)


class S_Brafar:
    def __init__(self, base_dir, wrong_code_dir_path, correct_code_dir_path, reference_dir_path,
                 ans_dir_path, sample_rate, exp_time):
        self.__base_dir = base_dir
        self.__correct_code_dir_path = correct_code_dir_path
        self.__reference_code_path = os.path.join(reference_dir_path, "reference.py")
        self.__global_path = None
        if os.path.exists(os.path.join(base_dir, "code", "global.py")):
            self.__global_path = os.path.join(base_dir, "code", "global.py")
        self.__exp_time = exp_time
        self.sample_rate = sample_rate
        self.__correct_code_path_list = get_file_list(correct_code_dir_path, sample_rate)
        self.__correct_code_path_list.append(self.__reference_code_path)
        self.__buggy_code_path_list = get_file_list(wrong_code_dir_path, 100)
        # self.__original_code = get_code(self.__buggy_code_path)
        self.__ans_dir_path = ans_dir_path
        self.__test_case_inputs = sorted(get_case_paths(ans_dir_path, "input"))
        self.__test_case_outputs = sorted(get_case_paths(ans_dir_path, "output"))
        self.init_correct_code_path()
        self.__repair_map = {}
        self.__failed_list = []
        self.run()

    def init_correct_code_path(self):
        for path in self.__buggy_code_path_list:
            code = get_code(path)
            if self.validate_repaired_code(code):
                self.__correct_code_path_list.append(path)

    def run(self):
        searcher = Searcher(self.__buggy_code_path_list, self.__correct_code_path_list)
        __program_map = searcher.get_program_map()
        search_time_map = searcher.get_search_time_map()
        match_ori_map = searcher.get_match_ori_map()
        i = 0
        for f_name in __program_map.keys():
            # print(f_name)
            repaired_code = ""
            repair_map = {"File Name": os.path.basename(f_name)}
            p_tree = ProgramTree(f_name)
            repair_map["Buggy Code"] = p_tree.get_p_code()
            repair_map["bug_ast_size"] = p_tree.get_ast_size()
            repair_map["Refactored Buggy Code"] = ""
            repair_map["Refactored Correct Code"] = ""
            repair_map["Bidirectional Refactoring Time"] = 0.0
            repair_map["Fault-Localization&Repair Time"] = 0.0
            repair_map["Search Time"] = search_time_map.get(f_name)
            repair_map["match_ori"] = match_ori_map.get(f_name)
            patch_size = 0
            func_maps = __program_map.get(f_name)
            repair_map["Original Correct File Name"] = {}
            s_time = time.time()
            for func_name in func_maps.keys():
                mapped_correct_code_path = func_maps.get(func_name)
                if mapped_correct_code_path is not None:
                    repair_map["Original Correct File Name"][func_name] = os.path.basename(mapped_correct_code_path)
                    re_func = Brafar(f_name, mapped_correct_code_path, func_name,
                                     self.__ans_dir_path, self.__global_path)
                    if re_func.get_repair_result():
                        repaired_code += re_func.get_repaired_code()
                        patch_size += p_tree.calculate_distance_func(func_name, re_func.get_repaired_code())
                        repaired_code += "\n"
                    repair_map["Bidirectional Refactoring Time"] += re_func.get_br_time()
                    repair_map["Fault-Localization&Repair Time"] += re_func.get_fl_repair_time()
                    repair_map["Refactored Buggy Code"] += re_func.get_refactored_buggy_code() + "\n"
                    repair_map["Refactored Correct Code"] += re_func.get_refactored_correct_code() + "\n"
            repair_result = self.validate_repaired_code(repaired_code)
            repair_map["Status"] = repair_result
            if not repair_result:
                self.__failed_list.append(f_name)
                repair_map["Repair Code"] = np.nan
                repair_map["RPS"] = np.nan
            else:
                repair_map["patch_size"] = patch_size
                repair_map["Repair Code"] = repaired_code
                if repair_map["bug_ast_size"] == 0:
                    repair_map["bug_ast_size"] = 1
                repair_map["RPS"] = float(patch_size) / float(repair_map["bug_ast_size"])
            e_time = time.time()
            repair_map["Total Time"] = repair_map["Search Time"] + float("%.4f" % (e_time - s_time))
            self.__repair_map[f_name] = repair_map
            # print(repair_result)

    def validate_repaired_code(self, repaired_code):
        repair_result = TestResult(repaired_code, self.__test_case_inputs, self.__test_case_outputs, self.__global_path)
        return repair_result.get_test_result()
        # print("The repair result is:", repair_result.get_test_result())
        # print("=============================The final Repair is as follows===================================")
        # print(self.__repaired_code)

    def output_to_csv(self):
        column = ["File Name", "Status", "Match (Ori Code)", "Buggy Code", "Refactored Buggy Code", "Refactored Correct Code",
                  "Original Correct File Name", "Repair", "Search Time", "Bidirectional Refactoring Time",
                  "Fault-Localization&Repair Time", "Total Time", "RPS"]
        statistics = []
        for value in self.__repair_map.values():
            statistics.append([value.get("File Name"), value.get("Status"), value.get("match_ori"), value.get("Buggy Code"),
                               value.get("Refactored Buggy Code"), value.get("Refactored Correct Code"),
                              value.get("Original Correct File Name"), value.get("Repair Code"), value.get("Search Time"),
                               value.get("Bidirectional Refactoring Time"), value.get("Fault-Localization&Repair Time"),
                               value.get("Total Time"), "%.5f" % value.get("RPS")])

        b = pd.DataFrame(statistics, columns=column)
        b.to_csv(os.path.join(self.__base_dir, "brafar_result_{}.csv".format(self.sample_rate)))

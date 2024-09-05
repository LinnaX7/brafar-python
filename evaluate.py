import ast
import math
import os
import re
import numpy as np
import pandas as pd
import argparse
from basic_framework.program_partition.program_builder import get_code, ProgramBuilder, syntax_check
from basic_framework.bidirectional_refactoring.cfs_distance import Distance
from basic_framework.core import get_case_paths
from basic_framework.distance import multi_func_code_distance, zss_code_ast_edit, zss_func_ast_size, ProgramTree
from basic_framework.fault_locator import TestResult
from basic_framework.program_partition.cfs import get_cfs_map, cfs_map_equal, get_func_map


def total_comparison(data_dir_path, tool_name):
    if tool_name == "brafar":
        tool_result = "brafar_result_100.csv"
    elif tool_name == "refactory":
        tool_result = "refactory_online.csv"
    else:
        tool_result = "clara_result.csv"
    sum_of_repair = 0
    sum_of_repair_time = 0.0
    sum_of_repair_rps = 0.0
    for i in range(5):
        df = pd.read_csv(os.path.join(data_dir_path, "question_{}".format(i + 1), tool_result))
        total_repair = 0
        total_repair_time = 0.0
        total_repair_rps = 0.0
        for ind in df.index:
            status = df.get("Status")[ind]
            if (isinstance(status, np.bool) and status == True) or (
                    isinstance(status, str) and status.startswith("success_")):
                total_repair += 1
                total_repair_time += df.get("Total Time")[ind]
                total_repair_rps += df.get("RPS")[ind]
        average_repair_time = total_repair_time / (float(total_repair))
        average_RPS = total_repair_rps / (float(total_repair))
        sum_of_repair += total_repair
        sum_of_repair_time += total_repair_time
        sum_of_repair_rps += total_repair_rps
        print(
            f"{tool_name} generated {total_repair} correct repairs for question {i + 1} with average repair time {average_repair_time} and average RPS {average_RPS}.")
    average_repair_time_All = sum_of_repair_time / (float(sum_of_repair))
    average_RPS_All = sum_of_repair_rps / (float(sum_of_repair))

    print(
        f"In total, {tool_name} generated {sum_of_repair} correct repairs with average repair time {average_repair_time_All} and average RPS {average_RPS_All}.")


def compare_rps(data_dir_path):
    column = ["File Name", "Refctory_RPS", "Brafar_RPS", "Clara_RPS"]
    statistics = []
    for i in range(5):
        file1 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
        file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "brafar_result_100.csv")
        file3 = os.path.join(data_dir_path, "question_{}".format(i + 1), "clara_result.csv")
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        df3 = pd.read_csv(file3)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        df2.sort_values("File Name", ascending=True, inplace=True)
        df2 = df2.reset_index(drop=True)
        df3.sort_values("File Name", ascending=True, inplace=True)
        df3 = df3.reset_index(drop=True)
        for ind in df1.index:
            col = [df1.get("File Name")[ind], df1.get("RPS")[ind], df2.get("RPS")[ind], df3.get("RPS")[ind]]
            statistics.append(col)
    b = pd.DataFrame(statistics, columns=column)
    b.to_csv(os.path.join(data_dir_path, "rps_compare.csv"))


def randomly_select_repair(data_dir_path):
    column = ["File Name", "Buggy Code", "Brafar_Repair", "Brafar_Result", "Brafar_RPS", "Refactory_Repair",
              "Refactory_Result", "Refactory_RPS", "Clara_Repair", "Clara_Result", "Clara_RPS"]
    statistics = []

    for i in range(5):
        file1 = os.path.join(data_dir_path, "question_{}".format(i + 1), "brafar_result_100.csv")
        file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
        file3 = os.path.join(data_dir_path, "question_{}".format(i+1), "clara_result.csv")
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        df3 = pd.read_csv(file3)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        df2.sort_values("File Name", ascending=True, inplace=True)
        df2 = df2.reset_index(drop=True)
        df3.sort_values("File Name", ascending=True, inplace=True)
        df3 = df3.reset_index(drop=True)
        print(df2.get("File Name")[0])
        if i != 4:
            random_numbers = np.random.randint(0, len(df1.index), size=int(len(df1.index) * 100 / 1783))
        else:
            random_numbers = np.random.randint(0, len(df1.index), size=int(len(df1.index) * 100 / 1783) + 1)
        for k in random_numbers:
            # print(df1.get("Status")[j])
            # print(df2.get("Status")[j])
            j = k
            while df1.get("Status")[j] != True or (not "success" in str(df2.get("Status")[j])):
                j = np.random.randint(0, len(df1.index), 1)[0]
                while j in random_numbers:
                    j = np.random.randint(0, len(df1.index), 1)[0]
            file_name = df1.get("File Name")[j]
            buggy_code = df1.get("Buggy Code")[j]
            brafar_repair = df1.get("Repair")[j]
            brafar_result = df1.get("Status")[j]
            brafar_rps = df1.get("RPS")[j]
            if df1.get("File Name")[j] != df2.get("File Name")[j]:
                print(j)
                print(df1.get("File Name")[j])
                print(df2.get("File Name")[j])
            refactory_repair = df2.get("Repair")[j]
            refactory_result = df2.get("Status")[j]
            refactory_rps = df2.get("RPS")[j]
            clara_repair = df3.get("Repair")[j]
            clara_result = df3.get("Status")[j]
            clara_RPS = df3.get("RPS")[j]
            statistics.append([file_name, buggy_code, brafar_repair, brafar_result, brafar_rps, refactory_repair,
                               refactory_result, refactory_rps, clara_repair, clara_result, clara_RPS])
    b = pd.DataFrame(statistics, columns=column)
    # statistic_show(b)
    b.to_csv(os.path.join(data_dir_path, "random_select_repairs.csv"))



def compare_repair_strategy(data_dir_path):
    brafar_rps_sum_all = 0
    brafar_repair_success_all = 0
    refactory_rps_sum_all = 0
    refactory_repair_success_all = 0
    no_need_refactoring_sum = 0
    for j in range(5):
        brafar_repair_success = 0
        brafar_rps_sum = 0
        refactory_repair_success = 0
        refactory_rps_sum = 0
        file1 = os.path.join(data_dir_path, "question_{}".format(j + 1), "brafar_result_100.csv")
        file2 = os.path.join(data_dir_path, "question_{}".format(j + 1), "refactory_online.csv")
        df2 = pd.read_csv(file2)
        df1 = pd.read_csv(file1)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        df2.sort_values("File Name", ascending=True, inplace=True)
        df2 = df2.reset_index(drop=True)
        for i in df2.index:
            match_ori = df2.get("Match (Ori Code)")[i]
            if match_ori == 1:
                no_need_refactoring_sum += 1
                if not math.isnan(df1.get("RPS")[i]):
                    brafar_rps_sum += df1.get("RPS")[i]
                    brafar_repair_success += 1
                if not math.isnan(df2.get("RPS")[i]):
                    refactory_rps_sum += df2.get("RPS")[i]
                    refactory_repair_success += 1
        print("===============================Assignment_{}===============================".format(j + 1))
        print(
            f"BRAFAR successed generate {brafar_repair_success} correct repair for the incorrect programs which didn't need refactoring in assignment {j + 1}.")
        # print(brafar_rps_sum_all)
        print(f"Average RPS: {float(brafar_rps_sum / float(brafar_repair_success))}")
        print(
            f"Refactry successed generate {refactory_repair_success} correct repair for the incorrect programs which didn't need refactoring in assignment {j+1}.")
        # print(refactory_repair_success_all)
        # print(refactory_rps_sum_all)
        print(f"Average RPS: {float(refactory_rps_sum / float(refactory_repair_success))}")

        # print(refactory_repair_success)
        # print(refactory_rps_sum)
        # print(float(refactory_rps_sum / float(refactory_repair_success)))
        # print(brafar_repair_success)
        # print(brafar_rps_sum)
        # print(float(brafar_rps_sum / float(brafar_repair_success)))
        brafar_repair_success_all += brafar_repair_success
        brafar_rps_sum_all += brafar_rps_sum
        refactory_repair_success_all += refactory_repair_success
        refactory_rps_sum_all += refactory_rps_sum
    print("===============================Total===============================")
    print(
        f"BRAFAR successed generate {brafar_repair_success_all} correct repair for the {no_need_refactoring_sum} incorrect programs which didn't need refactoring.")
    # print(brafar_rps_sum_all)
    print(f"Average RPS: {float(brafar_rps_sum_all / float(brafar_repair_success_all))}")
    print(
        f"Refactry successed generate {refactory_repair_success_all} correct repair for the {no_need_refactoring_sum} incorrect programs which didn't need refactoring.")
    # print(refactory_repair_success_all)
    # print(refactory_rps_sum_all)
    print(f"Average RPS: {float(refactory_rps_sum_all / float(refactory_repair_success_all))}")


def bidirectional_refactoring_evaluation(data_dir_path):
    count_w_r = 0
    count_wo_r = 0
    count_match_ori = 0
    count_match_rft = 0
    count_match_ccc = 0
    count_not_match_wo_r = 0
    column = ["File Name", "Target Method", "Buggy Code", "Lines of Code", "Control Flow Nodes",
              "Buggy Mutation", "Refactory Success Rate", "Refactory Time", "Refactory Edit Dist",
              "Buggy Guidance code", "Brafar Success Rate", "Guidance Time", "Brafar Edit Dist"]
    statistics = []
    statistics2 = []
    for i in range(5):
        file1 = os.path.join(data_dir_path, "question_{}".format(i + 1), "brafar_result_100.csv")
        file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        df2.sort_values("File Name", ascending=True, inplace=True)
        df2 = df2.reset_index(drop=True)
        wrong_folder = os.path.join(data_dir_path, "question_{}".format(i + 1), "code", "wrong")
        correct_folder = os.path.join(data_dir_path, "question_{}".format(i + 1), "code", "correct")
        reference_folder = os.path.join(data_dir_path, "question_{}".format(i + 1), "code", "reference")
        for ind in df2.index:
            file_name = df2.get("File Name")[ind]
            buggy_file = os.path.join(wrong_folder, df2.get("File Name")[ind])
            buggy_p = ProgramBuilder(get_code(buggy_file), df2.get("File Name")[ind])
            buggy_file_map = get_func_map(get_code(buggy_file))
            match_ori = df2.get("Match (Ori Code)")[ind]
            match_refactored = df2.get("Match (Rfty Code)")[ind]
            if match_ori == 1:
                count_match_ori += 1
            if match_refactored == 1:
                count_match_rft += 1
            if match_ori == 1 and match_refactored == 1:
                count_match_ccc += 1
            if match_ori == 0 and match_refactored == 1:
                if df2.get("Original Correct File Name")[ind] is not None:
                    buggy_correct_mix_p = ProgramBuilder(df2.get("Refactored Correct Code")[ind], "mix")
                    buggy_refactored_mix_p = ProgramBuilder(df1.get("Refactored Buggy Code")[ind], "mix")
                    ori_correct_file_name = eval(df2.get("Original Correct File Name")[ind])
                    flag = True
                    count = 0
                    for func_name in buggy_file_map:
                        if ori_correct_file_name.get(func_name) is not None:
                            if ori_correct_file_name.get(func_name) == "reference.py":
                                correct_file = os.path.join(reference_folder, "reference.py")
                            else:
                                correct_file = os.path.join(correct_folder, ori_correct_file_name.get(func_name))
                            correct_file_map = get_func_map(get_code(correct_file))
                            if not cfs_map_equal(get_cfs_map(buggy_file_map.get(func_name)),
                                                 get_cfs_map(correct_file_map.get(func_name))):
                                flag = False
                                count += 1
                    if not flag:
                        for func_name in buggy_file_map:
                            if ori_correct_file_name.get(func_name) is not None:
                                if ori_correct_file_name.get(func_name) == "reference.py":
                                    correct_file = os.path.join(reference_folder, "reference.py")
                                else:
                                    correct_file = os.path.join(correct_folder, ori_correct_file_name.get(func_name))
                                correct_file_map = get_func_map(get_code(correct_file))
                                if not cfs_map_equal(get_cfs_map(buggy_file_map.get(func_name)),
                                                     get_cfs_map(correct_file_map.get(func_name))):
                                    buggy_m = buggy_p.get_method(func_name)
                                    loc = buggy_m.lines
                                    cnt = len(buggy_m.struct_list)
                                    refactoring_time = (df2.get("Online Refactoring Time")[ind] + df2.get("GCR Time")[
                                        ind]) / float(count)
                                    br_time = df1.get("Bidirectional Refactoring Time")[ind] / float(count)
                                    buggy_refactored_m = buggy_refactored_mix_p.get_method(func_name)
                                    br_edit_dist = Distance(buggy_m.struct_node, buggy_refactored_m.struct_node).dist
                                    col = [file_name, func_name, buggy_file_map.get(func_name), loc, cnt,
                                           buggy_file_map.get(func_name), True, refactoring_time, 0.0,
                                           buggy_refactored_m.get_method_code(), True, br_time, br_edit_dist]
                                    statistics.append(col)
                    if flag:
                        count_wo_r += 1
                count_w_r += 1
            elif match_ori == 0 and match_refactored == 0:
                if df2.get("Original Correct File Name")[ind] is not None:
                    buggy_correct_mix_p = ProgramBuilder(df2.get("Refactored Correct Code")[ind], "mix")
                    buggy_refactored_mix_p = ProgramBuilder(df1.get("Refactored Buggy Code")[ind], "mix")
                    buggy_mutation_mix_p = ProgramBuilder(df2.get("Buggy Mutation")[ind], "mix")
                    ori_correct_file_name = eval(df2.get("Original Correct File Name")[ind])
                    flag = True
                    count = 0
                    for func_name in buggy_file_map:
                        if ori_correct_file_name.get(func_name) is not None:
                            if ori_correct_file_name.get(func_name) == "reference.py":
                                correct_file = os.path.join(reference_folder, "reference.py")
                            else:
                                correct_file = os.path.join(correct_folder, ori_correct_file_name.get(func_name))
                            correct_file_map = get_func_map(get_code(correct_file))
                            if not cfs_map_equal(get_cfs_map(buggy_file_map.get(func_name)),
                                                 get_cfs_map(correct_file_map.get(func_name))):
                                flag = False
                                count += 1
                    if not flag:
                        for func_name in buggy_file_map:
                            if ori_correct_file_name.get(func_name) is not None:
                                if ori_correct_file_name.get(func_name) == "reference.py":
                                    correct_file = os.path.join(reference_folder, "reference.py")
                                else:
                                    correct_file = os.path.join(correct_folder, ori_correct_file_name.get(func_name))
                                correct_file_map = get_func_map(get_code(correct_file))
                                if not cfs_map_equal(get_cfs_map(buggy_file_map.get(func_name)),
                                                     get_cfs_map(correct_file_map.get(func_name))):
                                    buggy_m = buggy_p.get_method(func_name)
                                    loc = buggy_m.lines
                                    cnt = len(buggy_m.struct_list)
                                    refactoring_success = cfs_map_equal(get_cfs_map(buggy_file_map.get(func_name)),
                                                                        get_cfs_map(buggy_correct_mix_p.get_method(
                                                                            func_name).get_method_code()))
                                    refactoring_time = df2.get("Online Refactoring Time")[ind] / float(count)
                                    buggy_mutation_m = buggy_mutation_mix_p.get_method(func_name)
                                    mutation_dist = Distance(buggy_m.struct_node, buggy_mutation_m.struct_node).dist
                                    br_time = df1.get("Bidirectional Refactoring Time")[ind] / float(count)
                                    buggy_refactored_m = buggy_refactored_mix_p.get_method(func_name)
                                    br_edit_dist = Distance(buggy_m.struct_node, buggy_refactored_m.struct_node).dist
                                    col = [file_name, func_name, buggy_file_map.get(func_name), loc, cnt,
                                           buggy_mutation_m.get_method_code(), refactoring_success, refactoring_time,
                                           mutation_dist,
                                           buggy_refactored_m.get_method_code(), True, br_time, br_edit_dist]
                                    statistics.append(col)
                                    if not refactoring_success:
                                        statistics2.append(col)
                    if flag:
                        count_wo_r += 1
            if match_ori == 1 and match_refactored != 1:
                print(buggy_file)
    b = pd.DataFrame(statistics, columns=column)
    b2 = pd.DataFrame(statistics2, columns=column)
    b.to_csv(os.path.join(data_dir_path, "bidirectional_refactoring_vs_refactory.csv"))
    b2.to_csv(os.path.join(data_dir_path, "bidirectional_refactoring_vs_structure_mutation.csv"))
    print(f"There are {count_match_ori} incorrect programs having a matching correct program with the identical "
          f"control-flow structure.")
    print(f"There are {count_wo_r} incorrect programs which actually were repaired by both tools without further "
          f"alignment by separately finding matching correct methods and combining them as references.")
    print("================================================Bidirectional Refactoring vs. Refactoring================================================")
    bidirectional_refactoring_vs_refactoring_show(b)
    print(
        "================================================Bidirectional Refactoring vs. Structure mutation================================================")
    bidirectional_refactoring_vs_structure_mutation_show(b2)


def bidirectional_refactoring_vs_refactoring_show(b: pd.DataFrame):
    data2 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Success Rate', 'Brafar Success Rate'], margins=True)
    data2.drop(data2.tail(2).index, inplace=True)
    print(data2)
    data4 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Time', 'Guidance Time'], margins=True)
    data4.drop(data4.tail(2).index, inplace=True)
    print(data4)


def bidirectional_refactoring_vs_structure_mutation_show(b: pd.DataFrame):
    data5 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Edit Dist', 'Brafar Edit Dist'], margins=True)
    data5.drop(data5.tail(2).index, inplace=True)
    print(data5)


class Evaluator:
    def __init__(self, data_dir_path, ques_no):
        self.ques_no = ques_no
        self.cur_folder = os.path.join(data_dir_path, f"question_{self.ques_no}")
        self.wrong_folder = os.path.join(self.cur_folder, "code", "wrong")
        self.correct_folder = os.path.join(self.cur_folder, "code", "correct")
        self.reference_folder = os.path.join(self.cur_folder, "code", "reference")
        self.ans_folder = os.path.join(self.cur_folder, "ans")
        self.refactory_result = os.path.join(self.cur_folder, "refactory_online.csv")
        self.brafar_result_100 = os.path.join(self.cur_folder, "brafar_result_100.csv")
        self.__test_case_inputs = sorted(get_case_paths(self.ans_folder, "input"))
        self.__test_case_outputs = sorted(get_case_paths(self.ans_folder, "output"))
        self.__chatgpt_result = os.path.join("ChatGPT4")

        self.__chatgpt_with_ref_result = os.path.join(self.__chatgpt_result, "output_ref", f"question_{self.ques_no}")
        self.__global_path = None
        if os.path.exists(os.path.join(self.cur_folder, "code", "global.py")):
            self.__global_path = os.path.join(self.cur_folder, "code", "global.py")

    def evaluate_all_correct_programs(self):
        for correct_file_name in os.listdir(self.correct_folder):
            if correct_file_name.endswith(".py"):
                correct_file = os.path.join(self.correct_folder, correct_file_name)
                correct_code = get_code(correct_file)
                test_r = self.validate_code(correct_code)
                if not test_r.get_test_result():
                    print(correct_file_name)

    def validate_code(self, repaired_code):
        test_result = TestResult(repaired_code, self.__test_case_inputs, self.__test_case_outputs, self.__global_path)
        return test_result

    def evaluate_mutation_result(self):
        df1 = pd.read_csv(self.refactory_result)
        df2 = pd.read_csv(self.brafar_result_100)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        df2.sort_values("File Name", ascending=True, inplace=True)
        df2 = df2.reset_index(drop=True)
        mutation_count = 0
        mutation_worse_count = 0
        refactory_rps_sum = 0
        brafar_rps_sum = 0
        mutation_repair_success = 0
        brafar_repair_success = 0
        failed_equal = 0
        for i in df1.index:
            match_ori = df1.get("Match (Ori Code)")[i]
            match_refactored = df1.get("Match (Rfty Code)")[i]
            file_name = df1.get("File Name")[i]
            if match_ori == 0 and match_refactored == 0:
                file_name = df1.get("File Name")[i]
                bug_ori_code = get_code(os.path.join(self.wrong_folder, file_name))
                bug_mutation_code = df1.get("Buggy Mutation")[i]
                bug_ori_test_result = self.validate_code(bug_ori_code)
                bug_ori_failed_test_cases = len(bug_ori_test_result.get_failed_input_cases())
                if bug_mutation_code == np.nan:
                    bug_mutation_failed_test_cases = len(self.__test_case_inputs)
                else:
                    bug_mutation_test_result = self.validate_code(bug_mutation_code)
                    bug_mutation_failed_test_cases = len(bug_mutation_test_result.get_failed_input_cases())
                if bug_mutation_failed_test_cases > bug_ori_failed_test_cases:
                    mutation_worse_count += 1
                if bug_mutation_failed_test_cases == bug_ori_failed_test_cases and bug_mutation_failed_test_cases == len(
                        self.__test_case_inputs):
                    failed_equal += 1
                mutation_count += 1
                if not math.isnan(df1.get("RPS")[i]):
                    # print(file_name)
                    refactory_rps_sum += df1.get("RPS")[i]
                    mutation_repair_success += 1
                if not math.isnan(df2.get("RPS")[i]):
                    brafar_rps_sum += df2.get("RPS")[i]
                    brafar_repair_success += 1
                if math.isnan(df2.get("RPS")[i]):
                    print(file_name)
        print("===============================Assignment_{}===============================".format(self.ques_no))
        print(
            f"BRAFAR successed generate {brafar_repair_success} correct repair for the incorrect programs which required structure mutation in assignment {self.ques_no}.")
        # print(brafar_rps_sum_all)
        print(f"Average RPS: {float(brafar_rps_sum / float(brafar_repair_success))}")
        print(f"After Refactory's structure mutation, {mutation_worse_count} of {mutation_count} incorrect programs failed more test cases.")
        print(
            f"Refactry successed generate {mutation_repair_success} correct repair for the incorrect programs which required structure mutation in assignment {self.ques_no}.")
        # print(refactory_repair_success_all)
        # print(refactory_rps_sum_all)
        print(f"Average RPS: {float(refactory_rps_sum / float(mutation_repair_success))}")
        return brafar_repair_success, brafar_rps_sum, mutation_repair_success, refactory_rps_sum


def structure_mutation_evaluation():
    total_brafar_repair_success = 0
    total_brafar_rps_sum = 0.0
    total_mutation_repair_success = 0
    total_refactory_rps_sum = 0.0
    for i in range(5):
        ev = Evaluator("data", i+1)
        b, r, m, s = ev.evaluate_mutation_result()
        total_brafar_repair_success += b
        total_brafar_rps_sum += r
        total_mutation_repair_success += m
        total_refactory_rps_sum += s
    print("===============================Total===============================")
    print(
        f"BRAFAR successed generate {total_brafar_repair_success} correct repair for the incorrect programs which required structure mutation.")
    # print(brafar_rps_sum_all)
    print(f"Average RPS: {float(total_brafar_rps_sum / float(total_brafar_repair_success))}")
    print(
        f"Refactry successed generate {total_mutation_repair_success} correct repair for the incorrect programs which required structure mutation.")
    # print(refactory_repair_success_all)
    # print(refactory_rps_sum_all)
    print(f"Average RPS: {float(total_refactory_rps_sum / float(total_mutation_repair_success))}")


if __name__ == '__main__':
    # bidirectional_refactoring_evaluation("data")
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data_dir", help="the path of the data directory.",
                        nargs='+', required=True)
    parser.add_argument("-e", "--evaluate", help="the evaluate target.",
                        nargs='+', default=None)
    args = parser.parse_args()

    if args.evaluate[0] == "OverallComparison":
        total_comparison(args.data_dir[0], "brafar")
        total_comparison(args.data_dir[0], "refactory")
        total_comparison(args.data_dir[0], "clara")

    if args.evaluate[0] == "RandomComparison":
        randomly_select_repair(args.data_dir[0])

    if args.evaluate[0] == "BidirectionalRefactoring":
        bidirectional_refactoring_evaluation("data")

    if args.evaluate[0] == "BidirectionalRefactoring":
        bidirectional_refactoring_evaluation("data")

    if args.evaluate[0] == "CompareRepairStrategy":
        compare_repair_strategy("data")

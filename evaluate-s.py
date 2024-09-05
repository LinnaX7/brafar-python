import ast
import math
import os
import re
import numpy as np
import pandas as pd

from basic_framework.program_partition.program_builder import get_code, ProgramBuilder, syntax_check
from basic_framework.bidirectional_refactoring.cfs_distance import Distance
from basic_framework.core import get_case_paths
from basic_framework.distance import multi_func_code_distance, zss_code_ast_edit, zss_func_ast_size, ProgramTree
from basic_framework.fault_locator import TestResult
from basic_framework.program_partition.cfs import get_cfs_map, cfs_map_equal, get_func_map




def remove_comments(code):
    code_node = ast.parse(code)
    i = 0
    while i < len(code_node.body):
        ast_node = code_node.body[i]
        # for ast_node in code_node.body:
        if not (isinstance(ast_node, ast.FunctionDef) or (
                isinstance(ast_node, ast.Import) or isinstance(ast_node, ast.ImportFrom))):
            code_node.body.remove(ast_node)
        else:
            i += 1
    code = ast.unparse(code_node)
    pattern = r'#.*$'
    code = re.sub(pattern, "", code, flags=re.MULTILINE | re.DOTALL)
    pattern = r"'''[^']*'''"
    code = re.sub(pattern, "", code, flags=re.MULTILINE | re.DOTALL)
    return code


# def compare_rps(data_dir_path):
#     column = ["Refctory_RPS", "Brafar_RPS"]
#     statistics = []
#     for i in range(5):
#         file1 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
#         file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "brafar_result_100.csv")
#         df1 = pd.read_csv(file1)
#         df2 = pd.read_csv(file2)
#         df1.sort_values("File Name", ascending=True, inplace=True)
#         df1 = df1.reset_index(drop=True)
#         df2.sort_values("File Name", ascending=True, inplace=True)
#         df2 = df2.reset_index(drop=True)
#         for ind in df1.index:
#             col = [df1.get("RPS")[ind], df2.get("RPS")[ind]]
#             statistics.append(col)
#     b = pd.DataFrame(statistics, columns=column)
#
#     data5 = pd.pivot_table(b, index='Control Flow Nodes',
#                            values=['Refactory Edit Dist', 'CFGuider Edit Dist'], margins=True)
#     data5.drop(data5.tail(2).index, inplace=True)
#     data5.plot(kind="line", marker='o')


def calculate_average_time(data_dir_path):
    all_time = 0.0
    all_p = 0
    for i in range(5):
        time_q = 0.0
        p_q = 0
        file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
        df2 = pd.read_csv(file2)
        for i in df2.index:
            status = df2.get("Status")[i]
            # if "success" in status:
            if not math.isnan(df2.get("Online Refactoring Time")[i]):
                t = float(df2.get("Online Refactoring Time")[i]) + float(df2.get("GCR Time")[i])
                if t < 1000:
                    time_q += t
                    # time_q += float(df2.get("Total Time")[i])
                    p_q += 1

        all_time += time_q
        all_p += p_q
        print("=================Assignment_{}===============================".format(i + 1))
        print(time_q / p_q)
    print(all_time / all_p)


def compare_show(data_dir_path):
    file = os.path.join(data_dir_path, "bidirectional_refactoring_evaluation_result.csv")
    file = os.path.join(data_dir_path, "structure_modification_comparison.csv")
    df = pd.read_csv(file)
    statistic_show(df)

def compare_mutation_rps(data_dir_path):
    mutation_count = 0
    mutation_repair_succuess = 0
    mutation_rps_sum = 0

    refactored_rps_sum = 0
    refactored_repair_succuess = 0

    brafar_count = 0
    brafar_repair_succuess = 0
    brafar_rps_sum = 0
    for i in range(5):
        file3 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory+_result.csv")
        file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
        file1 = os.path.join(data_dir_path, "question_{}".format(i + 1), "brafar_result_100.csv")
        df3 = pd.read_csv(file3)
        for i in df3.index:
            refactored_repair_succuess += 1
            refactored_rps_sum += df3.get("Refactory+_RPS")[i]
        df2 = pd.read_csv(file2)
        df1 = pd.read_csv(file1)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        df2.sort_values("File Name", ascending=True, inplace=True)
        df2 = df2.reset_index(drop=True)
        for i in df2.index:
            match_ori = df2.get("Match (Ori Code)")[i]
            match_refactored = df2.get("Match (Rfty Code)")[i]
            file_name = df2.get("File Name")[i]
            if match_ori == 0 and match_refactored == 0:
                mutation_count += 1
                if not math.isnan(df2.get("RPS")[i]):
                    mutation_repair_succuess += 1
                    mutation_rps_sum += df2.get("RPS")[i]
                if not math.isnan(df1.get("RPS")[i]):
                    brafar_rps_sum += df1.get("RPS")[i]
                    brafar_repair_succuess += 1

    print(mutation_count)
    print(mutation_rps_sum)
    print(mutation_repair_succuess)
    print(refactored_rps_sum)
    print(refactored_repair_succuess)
    print(brafar_rps_sum)
    print(brafar_repair_succuess)


def randomly_select_repair(data_dir_path):
    column = ["File Name", "Buggy Code", "Brafar_Repair", "Brafar_Result", "Brafar_RPS", "Refactory_Repair",
              "Refactory_Result", "Refactory_RPS"]
    statistics = []

    for i in range(5):
        file1 = os.path.join(data_dir_path, "question_{}".format(i + 1), "brafar_result_100.csv")
        file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        df2.sort_values("File Name", ascending=True, inplace=True)
        df2 = df2.reset_index(drop=True)
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
                while j not in random_numbers:
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
            statistics.append([file_name, buggy_code, brafar_repair, brafar_result, brafar_rps, refactory_repair,
                               refactory_result, refactory_rps])
    b = pd.DataFrame(statistics, columns=column)
    # statistic_show(b)
    b.to_csv(os.path.join(data_dir_path, "random_select_repairs.csv"))


def calculate_mutated(data_dir_path):
    count_match_ori = 0
    count_match_rft = 0
    count_match_ccc = 0
    count_1 = 0
    count_refactored = 0
    count_mutate = 0
    count_failed = 0
    for i in range(5):
        # file1 = os.path.join(data_dir_path, "question_{}".format(i + 1), "brafar_result_100.csv")
        file2 = os.path.join(data_dir_path, "question_{}".format(i + 1), "refactory_online.csv")
        df2 = pd.read_csv(file2)
        for ind in df2.index:
            match_ori = df2.get("Match (Ori Code)")[ind]
            match_refactored = df2.get("Match (Rfty Code)")[ind]
            if match_ori == 1:
                count_match_ori += 1
            if match_refactored == 1:
                count_match_rft += 1
            if match_ori == 1 and match_refactored == 1:
                count_match_ccc += 1
            if match_ori == 0:
                count_1 += 1
            if match_ori == 0 and match_refactored == 1:
                count_refactored += 1
            elif match_ori == 0 and match_refactored == 0:
                count_mutate += 1
            elif match_ori == 0:
                count_failed += 1
    print(count_1)
    print(count_refactored)
    print(count_mutate)
    print(count_failed)


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
    # statistic_show(b)
    b.to_csv(os.path.join(data_dir_path, "bidirectional_refactoring_evaluation_result.csv"))
    b2.to_csv(os.path.join(data_dir_path, "structure_modification_comparison.csv"))
    print(count_w_r)
    print(count_wo_r)
    print(count_match_ori)
    print(count_match_rft)
    print(count_match_ccc)


def get_chatgpt_code_3(file):
    code = ""
    with open(file, "r") as f:
        line = f.readline()
        flag = False
        while line:
            if flag and not line.startswith("'''"):
                code += line
            elif not flag and line.startswith("'''"):
                flag = True
            elif flag and line.startswith("'''"):
                break
            line = f.readline()
    return remove_comments(code)


def get_chatgpt_code_2(file):
    code = ""
    with open(file, "r") as f:
        line = f.readline()
        flag = False
        while line:
            if flag and not line.startswith("'''"):
                code += line
            elif not flag and line.startswith("'''"):
                flag = True
            elif flag and line.startswith("'''"):
                break
            line = f.readline()
    return remove_comments(code)


def get_chatgpt_code(file):
    code = ""
    with open(file, "r") as f:
        line = f.readline()
        flag = False
        while line:
            if flag and not line.startswith("```"):
                code += line
            elif not flag and line.startswith("```"):
                flag = True
            elif flag and line.startswith("```"):
                break
            line = f.readline()
    return remove_comments(code)


class Evaluator:
    def __init__(self, data_dir_path, ques_dir):
        cur_question = ques_dir
        self.cur_question = ques_dir
        self.cur_folder = os.path.join(data_dir_path, cur_question)
        self.wrong_folder = os.path.join(self.cur_folder, "code", "wrong")
        self.correct_folder = os.path.join(self.cur_folder, "code", "correct")
        self.reference_folder = os.path.join(self.cur_folder, "code", "reference")
        self.ans_folder = os.path.join(self.cur_folder, "ans")
        self.refactory_result = os.path.join(self.cur_folder, "refactory_online.csv")
        self.brafar_result_100 = os.path.join(self.cur_folder, "brafar_result_100.csv")
        self.__test_case_inputs = sorted(get_case_paths(self.ans_folder, "input"))
        self.__test_case_outputs = sorted(get_case_paths(self.ans_folder, "output"))
        self.__chatgpt_result = os.path.join("ChatGPT4")

        self.__chatgpt_with_ref_result = os.path.join(self.__chatgpt_result, "output_ref", self.cur_question)
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

    def evaluate_chatgpt(self, target_folder):
        self.__chatgpt_ori_result = os.path.join(self.__chatgpt_result, target_folder, self.cur_question)
        column = ["File Name", "Buggy Code", "ChatGPT Result", "Repair Result", "RPS"]
        statistics = []
        for file in os.listdir(self.__chatgpt_ori_result):
            if file.endswith(".py"):
                col = []
                is_syntax_error = False
                chatgpt_result = get_chatgpt_code(os.path.join(self.__chatgpt_ori_result, file))
                if syntax_check(chatgpt_result) is None:
                    print(file)
                    is_syntax_error = True
                    # continue
                if chatgpt_result == "":
                    chatgpt_result = get_chatgpt_code_2(os.path.join(self.__chatgpt_ori_result, file))
                    if syntax_check(chatgpt_result) is None:
                        print(file)
                        is_syntax_error = True
                        # continue
                if chatgpt_result == "":
                    chatgpt_result = get_chatgpt_code_3(os.path.join(self.__chatgpt_ori_result, file))
                    if syntax_check(chatgpt_result) is None:
                        print(file)
                        is_syntax_error = True
                        # continue
                if chatgpt_result == "":
                    print(file)
                    continue
                buggy_code = get_code(os.path.join(self.wrong_folder, file))
                if is_syntax_error:
                    col = [file, buggy_code, chatgpt_result, False, np.nan]
                    statistics.append(col)
                else:

                    repair_r = self.validate_code(chatgpt_result).get_test_result()
                    patch_size = multi_func_code_distance(buggy_code, chatgpt_result, zss_code_ast_edit)
                    RPS = float(patch_size) / float(zss_func_ast_size(buggy_code))
                    if not repair_r:
                        RPS = np.nan
                    col = [file, buggy_code, chatgpt_result, repair_r, RPS]
                    statistics.append(col)
        b = pd.DataFrame(statistics, columns=column)
        # statistic_show(b)
        b.to_csv(os.path.join(self.__chatgpt_ori_result, "chatgpt_result.csv"))

    def evaluate_chatgpt_with_ref(self):
        column = ["File Name", "Buggy Code", "ChatGPT Result", "Repair Result", "RPS"]
        statistics = []
        reference_code = get_code(os.path.join(self.reference_folder, "reference.py")).replace("\n", "").replace(" ",
                                                                                                                 "")
        count = 0
        for file in os.listdir(self.__chatgpt_with_ref_result):
            if file.endswith(".py"):
                col = []
                chatgpt_result = get_chatgpt_code(os.path.join(self.__chatgpt_with_ref_result, file))
                if syntax_check(chatgpt_result) is None:
                    print(file)
                    continue
                if chatgpt_result == "":
                    chatgpt_result = get_chatgpt_code_2(os.path.join(self.__chatgpt_with_ref_result, file))
                    if syntax_check(chatgpt_result) is None:
                        print(file)
                        continue
                if chatgpt_result == "":
                    chatgpt_result = get_chatgpt_code_3(os.path.join(self.__chatgpt_with_ref_result, file))
                    if syntax_check(chatgpt_result) is None:
                        print(file)
                        continue
                if chatgpt_result == "":
                    print(file)
                    continue
                temp = chatgpt_result.replace("\n", "").replace(" ", "")
                if temp == reference_code:
                    count += 1
                buggy_code = get_code(os.path.join(self.wrong_folder, file))
                repair_r = self.validate_code(chatgpt_result).get_test_result()
                patch_size = multi_func_code_distance(buggy_code, chatgpt_result, zss_code_ast_edit)
                RPS = float(patch_size) / float(zss_func_ast_size(buggy_code))
                if not repair_r:
                    RPS = np.nan
                col = [file, buggy_code, chatgpt_result, repair_r, RPS]
                statistics.append(col)
        print("overfitting:{}".format(count))
        b = pd.DataFrame(statistics, columns=column)
        # statistic_show(b)
        b.to_csv(os.path.join(self.__chatgpt_with_ref_result, "chatgpt_result.csv"))

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
        better_count = 0
        RPS_count = 0
        mutation_repair_succuess = 0
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
                    mutation_repair_succuess += 1
                if not math.isnan(df2.get("RPS")[i]):
                    brafar_rps_sum += df2.get("RPS")[i]
                if df1.get("RPS")[i] < df2.get("RPS")[i] + 0.01:
                    print(file_name)
                    better_count += 1
            # if df2.get("RPS")[i] - df1.get("RPS")[i]>0.002:
            #     print(file_name)
            #     print(df1.get("RPS")[i])
            #     print(df2.get("RPS")[i])
            #     RPS_count += 1
        print()
        print(mutation_count)
        print(mutation_worse_count)
        print(failed_equal)
        print(refactory_rps_sum / mutation_repair_succuess)
        print(brafar_rps_sum / mutation_count)
        print(better_count)
        print(RPS_count)


def statistic_show(b: pd.DataFrame):
    # b.mean()
    # data1 = pd.pivot_table(b, index='Lines of Code',
    #                        values=['Refactory Success Rate', 'Brafar Success Rate'], margins=True)
    # # data1.drop(data1.tail(2).index, inplace=True)
    # print(data1)
    # data1.plot(kind="line", marker='o')
    # print(data1)
    data2 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Success Rate', 'Brafar Success Rate'], margins=True)
    print(data2)
    data2.drop(data2.tail(2).index, inplace=True)
    print(data2)
    data4 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Time', 'Guidance Time'], margins=True)
    data4.drop(data4.tail(2).index, inplace=True)
    print(data4)
    data5 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Edit Dist', 'Brafar Edit Dist'], margins=True)
    data5.drop(data5.tail(2).index, inplace=True)
    print(data5)

    data3 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Time', 'Guidance Time'], margins=True)
    data3.drop(data3.tail(2).index, inplace=True)

    print(data3)
    data4 = pd.pivot_table(b, index='Lines of Code',
                           values=['Refactory Time', 'Guidance Time'], margins=True)
    data4.drop(data4.tail(2).index, inplace=True)

    data5 = pd.pivot_table(b, index='Control Flow Nodes',
                           values=['Refactory Edit Dist', 'Brafar Edit Dist'], margins=True)
    data5.drop(data5.tail(2).index, inplace=True)
    # data5.plot(kind="line", marker='o')
    print(data5)
    data6 = pd.pivot_table(b, index='Lines of Code',
                           values=['Refactory Edit Dist', 'Brafar Edit Dist'], margins=True)
    data6.drop(data6.tail(2).index, inplace=True)
    # data6.plot(kind="line", marker='o')
    # plt.show()


def output_to_csv(__base_dir, __repair_map):
    column = ["File Name", "Status", "Repair", "Total Time", "Patch Size", "RPS"]
    statistics = []
    for value in __repair_map.values():
        statistics.append([value.get("File Name"), value.get("Status"), value.get("Repair"),
                           value.get("Total Time"), value.get("Patch Size"), value.get("RPS")])

    b = pd.DataFrame(statistics, columns=column)
    b.to_csv(os.path.join(__base_dir, f"clara_result.csv"))


def process_clara_result_2(data_dir_path):
    wrong_folder = os.path.join(data_dir_path, "question_{}".format(2), "code", "wrong")
    function_list = ["unique_day", "unique_month", "contains_unique_day"]
    file1 = os.path.join(data_dir_path, "question_{}".format(2), f"clara_result_{function_list[0]}.csv")
    df1 = pd.read_csv(file1)
    file2 = os.path.join(data_dir_path, "question_{}".format(2), f"clara_result_{function_list[1]}.csv")
    df2 = pd.read_csv(file2)
    file3 = os.path.join(data_dir_path, "question_{}".format(2), f"clara_result_{function_list[2]}.csv")
    df3 = pd.read_csv(file3)
    df1.sort_values("File Name", ascending=True, inplace=True)
    df1 = df1.reset_index(drop=True)
    df2.sort_values("File Name", ascending=True, inplace=True)
    df2 = df2.reset_index(drop=True)
    df3.sort_values("File Name", ascending=True, inplace=True)
    df3 = df3.reset_index(drop=True)
    repair_map_sum = {}
    for j in df1.index:
        repair_map = {}
        file_name = df1.get("File Name")[j]
        repair_map["File Name"] = file_name
        repair_map["Status"] = df1.get("Status")[j] and df2.get("Status")[j] and df3.get("Status")[j]
        repair_map["Repair"] = str(df1.get("Repair")[j]) + str(df2.get("Repair")[j]) + str(df3.get("Repair")[j])
        repair_map["Total Time"] = df1.get("Total Time")[j] + df2.get("Total Time")[j] + df3.get("Total Time")[j]
        repair_map["Patch Size"] = df1.get("Patch Size")[j] + df2.get("Patch Size")[j] + df3.get("Patch Size")[j]
        wrong_file_path = os.path.join(wrong_folder, file_name)
        p_tree = ProgramTree(wrong_file_path)
        bug_ast_size = p_tree.get_ast_size()
        if bug_ast_size == 0:
            bug_ast_size = 1
        repair_map["RPS"] = float(repair_map["Patch Size"]) / float(bug_ast_size)
        repair_map_sum[file_name] = repair_map
    output_to_csv(os.path.join(data_dir_path, "question_{}".format(2)), repair_map_sum)


def process_clara_result(data_dir_path):
    for i in range(5):
        wrong_folder = os.path.join(data_dir_path, "question_{}".format(i + 1), "code", "wrong")
        file = os.path.join(data_dir_path, "question_{}".format(i + 1), "clara_result.csv")
        df = pd.read_csv(file)
        repair_map_sum = {}
        count = 0
        for j in df.index:
            repair_map = {}
            file_name = df.get("File Name")[j]
            repair_map["File Name"] = file_name
            repair_map["Status"] = df.get("Status")[j]
            repair_map["Repair"] = df.get("Repair")[j]
            repair_map["Total Time"] = df.get("Total Time")[j]
            repair_map["Patch Size"] = df.get("Patch Size")[j]
            wrong_file_path = os.path.join(wrong_folder, file_name)
            p_tree = ProgramTree(wrong_file_path)
            bug_ast_size = p_tree.get_ast_size()
            if bug_ast_size == 0:
                bug_ast_size = 1
            if not np.isnan(df.get("Patch Size")[j]) and df.get("Patch Size")[j] == 0:
                repair_map["RPS"] = np.nan
                repair_map["Status"] = False
                repair_map["Total Time"] = np.nan
                count += 1
            else:
                # bug_ast_size = get_code_size(os.path.join(wrong_folder, file_name))
                if bug_ast_size == 0:
                    bug_ast_size = 1
                # repair_map["RPS"] = df.get("RPS")[j]
                repair_map["RPS"] = float(repair_map["Patch Size"]) / float(bug_ast_size)
            repair_map_sum[file_name] = repair_map
        output_to_csv(os.path.join(data_dir_path, "question_{}".format(i + 1)), repair_map_sum)
        print(count)

def generate_random_s(data_dir_path):
    column = ["File Name", "Buggy Code", "Brafar_Repair", "Brafar_Result", "Brafar_RPS", "Refactory_Repair",
              "Refactory_Result", "Refactory_RPS", "Clara_Repair", "Clara_Result", "Clara_RPS"]
    statistics = []
    file = "/Users/seg_zt/Desktop/brafar-system/data/random_select_repairs.csv"
    df = pd.read_csv(file)
    for i in df.index:
        file_name = df.get("File Name")[i]
        buggy_code = df.get("Buggy Code")[i]
        brafar_repair = df.get("Brafar_Repair")[i]
        brafar_result = df.get("Brafar_Result")[i]
        brafar_RPS = df.get("Brafar_RPS")[i]
        refactory_repair = df.get("Refactory_Repair")[i]
        refactory_result = df.get("Refactory_Result")[i]
        refactory_RPS = df.get("Refactory_RPS")[i]
        if i<32:
            file1 = os.path.join(data_dir_path, "question_1", "clara_result.csv")
        elif i<56:
            file1 = os.path.join(data_dir_path, "question_2", "clara_result.csv")
        elif i<73:
            file1 = os.path.join(data_dir_path, "question_3", "clara_result.csv")
        elif i<93:
            file1 = os.path.join(data_dir_path, "question_4", "clara_result.csv")
        else:
            file1 = os.path.join(data_dir_path, "question_5", "clara_result.csv")
        df1 = pd.read_csv(file1)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        index = file_name.split("_")[2].replace(".py", "")
        j = int(index)-1
        clara_repair = df1.get("Repair")[j]
        clara_result = df1.get("Status")[j]
        clara_RPS = df1.get("RPS")[j]
        statistics.append([file_name, buggy_code, brafar_repair, brafar_result, brafar_RPS, refactory_repair,
                           refactory_result, refactory_RPS, clara_repair, clara_result, clara_RPS])
    b = pd.DataFrame(statistics, columns=column)
    # statistic_show(b)
    b.to_csv(os.path.join(data_dir_path, "random_select_repairs.csv"))


def generate_random_r(data_dir_path):
    column = ["File Name", "Buggy Code", "Brafar_Repair", "Brafar_Result", "Brafar_RPS", "Refactory_Repair",
              "Refactory_Result", "Refactory_RPS", "Clara_Repair", "Clara_Result", "Clara_RPS"]
    statistics = []
    file = "/Users/seg_zt/Desktop/brafar-system/data/random_select_repairs.csv"
    df = pd.read_csv(file)
    count = 0
    for i in df.index:
        file_name = df.get("File Name")[i]
        if i<32:
            d = 1
        elif i<56:
            d = 2
        elif i<73:
            d = 3
        elif i<93:
            d = 4
        else:
            d = 5
        file1 = os.path.join(data_dir_path, f"question_{d}", "refactory_online.csv")
        correct_folder = os.path.join(data_dir_path, f"question_{d}", "code", "correct")
        wrong_folder = os.path.join(data_dir_path, f"question_{d}", "code", "wrong")
        reference_folder = os.path.join(data_dir_path, f"question_{d}", "code", "reference")
        df1 = pd.read_csv(file1)
        df1.sort_values("File Name", ascending=True, inplace=True)
        df1 = df1.reset_index(drop=True)
        index = file_name.split("_")[2].replace(".py", "")
        j = int(index)-1
        match_ori = df1.get("Match (Ori Code)")[j]
        match_refactored = df1.get("Match (Rfty Code)")[j]
        buggy_file = os.path.join(wrong_folder, df1.get("File Name")[j])

        if match_ori == 0:
            if df1.get("Original Correct File Name")[j] is not None:
                ori_correct_file_name = eval(df1.get("Original Correct File Name")[j])
                buggy_file_map = get_func_map(get_code(buggy_file))
                flag = True
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
                            print(df1.get("File Name")[j])
    print(count)

        # clara_repair = df1.get("Repair")[j]
        # clara_result = df1.get("Status")[j]
        # clara_RPS = df1.get("RPS")[j]
        # statistics.append([file_name, buggy_code, brafar_repair, brafar_result, brafar_RPS, refactory_repair,
        #                    refactory_result, refactory_RPS, clara_repair, clara_result, clara_RPS])
    # b = pd.DataFrame(statistics, columns=column)
    # # statistic_show(b)
    # b.to_csv(os.path.join(data_dir_path, "random_select_repairs.csv"))




if __name__ == '__main__':
    # Bidirectional Refactoring Evaluation
    # bidirectional_refactoring_evaluation("data")
    # Repair Strategy Evaluation
    # compare_repair_strategy("data")
    # compare_mutation_rps("data")
    # calculate_mutated("data")
    # compare_show("data")
    # generate_random_r("data")
    # process_clara_result_2("data")
    # total_comparison("data", "clara")
    # compare_rps("data")
    # code = get_chatgpt_code_2("brafar-python/test1.py")
    # calculate_mutated("data")
    # ev = Evaluator("data", "question_5")
    # ev.evaluate_all_correct_programs()
    # test_result1 = ev.validate_code(get_code("brafar-python/test1.py"))
    # test_result2 = ev.validate_code(get_code("brafar-python/test2.py"))
    # print(test_result1.get_test_result())
    # print(test_result2.get_test_result())
    # ev.evaluate_mutation_result()
    # ev.evaluate_chatgpt("output_testsuite")
    # ev.evaluate_chatgpt_with_ref()
    # randomly_select_repair("data")
    # calculate_average_time("data")
    # print(remove_comments("def remove_extras(lst):\n\treturn 3\nprint(remove_extras([1, 5, 1, 1, 3, 2]))"))
    # compare_mutation_rps("data")
    compare_show("data")
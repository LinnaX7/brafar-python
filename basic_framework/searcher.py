import time
from basic_framework.bidirectional_refactoring.mapping import RoughMapping, LoopMapping
from basic_framework.program_partition.program_builder import get_programs, get_programs_map
from basic_framework.distance import lev_multi_func_code_distance, smt_lev_multi_func_code_distance
from basic_framework.program_partition.cfs import cfs_map_equal, get_cfs_map, get_func_map
from basic_framework.program_partition.utils import regularize
#
# def search_kth_max_match(k, buggy_method, correct_ps):
#     lp_map = 0
#     map_ps = []
#     lp_edit_distance = 100
#     s_time = time.time()
#     need_refactor = True
#     for correct_p in correct_ps:
#         correct_m = correct_p.methods.get(buggy_method.m_name)
#         if correct_m is None:
#             continue
#         if correct_m.is_containing_inner_func():
#             continue
#         if buggy_method.cfs == correct_m.cfs:
#             if need_refactor:
#                 map_ps.clear()
#             map_ps.append((correct_m.f_name, correct_m, 1))
#             lp_edit_distance = 0
#             need_refactor = False
#         elif need_refactor:
#             rough_map = RoughMapping(buggy_method.cs_node, correct_m.cs_node)
#             rough_map.mapping()
#             loop_map = LoopMapping(buggy_method.cs_node, correct_m.cs_node)
#             loop_map.mapping()
#             cur_lp_edit_distance = len(loop_map.src_nodes) + len(loop_map.dst_nodes) - 2 * loop_map.mapping_score
#             if cur_lp_edit_distance < lp_edit_distance:
#                 lp_map = loop_map.mapping_score
#                 lp_edit_distance = cur_lp_edit_distance
#                 lp_map_rate = float(loop_map.mapping_score) / float(
#                     max(len(loop_map.src_nodes), len(loop_map.dst_nodes)))
#                 map_ps.clear()
#                 map_ps.append((correct_m.f_name, correct_m, rough_map.mapping_score,
#                                float(rough_map.mapping_score) / float(
#                                    max(len(rough_map.src_nodes), len(rough_map.dst_nodes)))))
#             elif cur_lp_edit_distance == lp_edit_distance:
#                 map_ps.append((correct_m.f_name, correct_m, rough_map.mapping_score,
#                                float(rough_map.mapping_score) / float(
#                                    max(len(rough_map.src_nodes), len(rough_map.dst_nodes)))))
#     map_ps = sorted(map_ps, key=lambda x: x[2], reverse=True)
#     new_map_ps = []
#     for map_p in map_ps:
#         if len(map_p[1].get_call_funcs()) == len(buggy_method.get_call_funcs()):
#             new_map_ps.append(map_p)
#     if len(new_map_ps) == 0:
#         new_map_ps = map_ps
#     # if len(new_map_ps) > 100:
#     #     new_map_ps = new_map_ps[0:k]
#     end_time = time.time()
#     kth_ps = []
#     kth_ps_codes = []
#     for map_p in new_map_ps:
#         kth_ps.append(map_p[0])
#         kth_ps_codes.append(map_p[1].get_method_code())
#     return kth_ps, kth_ps_codes, float("%.4f" % (end_time - s_time))
#
#
# class Searcher:
#     def __init__(self, buggy_code_path_list, correct_code_path_list):
#         self.k = 5
#         self.__buggy_programs = get_programs(buggy_code_path_list)
#         self.__correct_programs = get_programs(correct_code_path_list)
#         self.__program_maps = {}
#         self.__search_time_maps = {}
#         self.run()
#
#     def run(self):
#         i = 0
#         for buggyP in self.__buggy_programs:
#             func_map = {}
#             search_time = 0
#             p_tree = ProgramTree(buggyP.get_f_name())
#             for func_name in buggyP.methods.keys():
#                 k_th_closest_maps, kth_ps_codes, ss_time = search_kth_max_match(
#                     self.k, buggyP.get_method(func_name), self.__correct_programs)
#                 s_time = time.time()
#                 _, index = p_tree.get_closest_func(func_name, kth_ps_codes)
#                 e_time = time.time()
#                 func_map[func_name] = k_th_closest_maps[index]
#                 search_time += ss_time
#                 search_time += float("%.4f" % (e_time - s_time))
#             self.__program_maps[buggyP.f_name] = func_map
#             self.__search_time_maps[buggyP.f_name] = search_time
#             i += 1
#             # if i>5:
#             #     return
#
#     def get_program_maps(self):
#         return self.__program_maps
#
#     def get_search_time_maps(self):
#         return self.__search_time_maps


def get_dir_codes(code_path_list):
    code_map = {}
    for code_path in code_path_list:
        code = ""
        # print(code_path)
        with open(code_path, "r") as f:
            code += f.read()
        code = regularize(code)
        code_map[code_path] = code
    return code_map


def get_corr_func_list_map(corr_code_map):
    corr_func_list_map = {}
    for file_name, corr_code in corr_code_map.items():
        func_code_map = get_func_map(corr_code)

        for func_name in func_code_map.keys():
            func_code = func_code_map[func_name]
            if func_name not in corr_func_list_map.keys():
                corr_func_list_map[func_name] = []
            corr_func_list_map[func_name].append((file_name, func_code))

    max_len = max([len(corr_func_list_map[func_name]) for func_name in corr_func_list_map.keys()])
    del_func_name_list = []
    for func_name in corr_func_list_map.keys():
        if max_len - len(corr_func_list_map[func_name]) > 5:
            del_func_name_list.append(func_name)

    for func_name in del_func_name_list:
        del corr_func_list_map[func_name]

    return corr_func_list_map


def cfs_search_func(buggy_method, correct_ps):
    lp_map = 0
    map_ps = []
    lp_edit_distance = 100
    need_refactor = True
    selected_correct_ps = []
    for correct_p in correct_ps:
        correct_m = correct_p.methods.get(buggy_method.m_name)
        if correct_m is None:
            continue
        if correct_m.is_containing_inner_func():
            continue
        if correct_m.get_call_funcs() == buggy_method.get_call_funcs():
            selected_correct_ps.append(correct_p)
    if len(selected_correct_ps) == 0:
        selected_correct_ps = correct_ps
    for correct_p in selected_correct_ps:
        correct_m = correct_p.methods.get(buggy_method.m_name)
        if correct_m is None:
            continue
        if correct_m.is_containing_inner_func():
            continue
        if buggy_method.cfs == correct_m.cfs:
            if need_refactor:
                map_ps.clear()
            map_ps.append((correct_m.f_name, correct_m, 1))
            lp_edit_distance = 0
            need_refactor = False
        elif need_refactor:
            rough_map = RoughMapping(buggy_method.cs_node, correct_m.cs_node)
            rough_map.mapping()
            loop_map = LoopMapping(buggy_method.cs_node, correct_m.cs_node)
            loop_map.mapping()
            cur_lp_edit_distance = len(loop_map.src_nodes) + len(loop_map.dst_nodes) - 2 * loop_map.mapping_score
            if cur_lp_edit_distance < lp_edit_distance:
                lp_map = loop_map.mapping_score
                lp_edit_distance = cur_lp_edit_distance
                lp_map_rate = float(loop_map.mapping_score) / float(
                    max(len(loop_map.src_nodes), len(loop_map.dst_nodes)))
                map_ps.clear()
                map_ps.append((correct_m.f_name, correct_m, rough_map.mapping_score,
                               float(rough_map.mapping_score) / float(
                                   max(len(rough_map.src_nodes), len(rough_map.dst_nodes)))))
            elif cur_lp_edit_distance == lp_edit_distance:
                map_ps.append((correct_m.f_name, correct_m, rough_map.mapping_score,
                               float(rough_map.mapping_score) / float(
                                   max(len(rough_map.src_nodes), len(rough_map.dst_nodes)))))
    map_ps = sorted(map_ps, key=lambda x: x[2], reverse=True)
    new_map_ps = []
    for map_p in map_ps:
        if map_p[1].is_recursive() and not buggy_method.is_recursive():
            continue
        new_map_ps.append(map_p)
    if len(new_map_ps) == 0:
        new_map_ps = map_ps
    rc_list = []
    for map_p in new_map_ps:
        rc = (map_p[1].get_method_code(), map_p[0])
        rc_list.append(rc)
    return rc_list


def first_search(bug_code, fname_corr_code):
    # extract func definition from bug code
    bug_func_map = get_func_map(bug_code)
    corr_func_list_map = get_corr_func_list_map(fname_corr_code)
    result = True
    rc_list_map = {}
    for func_name, bug_func_code in bug_func_map.items():
        if corr_func_list_map.get(func_name) is not None:
            corr_func_code_map = dict(corr_func_list_map[func_name])
            rc_list = first_search_func(bug_func_code, corr_func_code_map)
            rc_list_map[func_name] = rc_list
        else:
            rc_list = []
        if len(rc_list) == 0:
            result = False
    return rc_list_map, result


def first_search_func(bug_func_code, fname_corr_func_code):
    rc_list = []
    bug_cfs_map = get_cfs_map(bug_func_code)
    # build min binary heap
    for fname, corrCode in fname_corr_func_code.items():
        rc = (corrCode, fname)
        corr_cfs_map = get_cfs_map(corrCode)
        if cfs_map_equal(bug_cfs_map, corr_cfs_map):
            rc_list.append(rc)
    return rc_list


def astar_get_cls_rc(bug_code, rc_list_map):
    bug_func_map = get_func_map(bug_code)
    file_map = {}

    for func_name, bug_func_code in bug_func_map.items():
        func_rc_list = rc_list_map[func_name]
        best_func_c_f_name = astar_get_cls_func_rc(bug_func_code, func_rc_list)
        file_map[func_name] = best_func_c_f_name
    return file_map


def astar_get_cls_func_rc(bug_func_code, rc_list):
    # choose best one based on ted
    min_ted, best_f_name = None, None
    for rc in rc_list:
        if min_ted is None:
            min_ted = lev_multi_func_code_distance(bug_func_code, rc[0])
            best_f_name = rc[1]
        else:
            ted = smt_lev_multi_func_code_distance(bug_func_code, rc[0], min_ted)
            if ted < min_ted:
                min_ted = ted
                best_f_name = rc[1]
    return best_f_name


class Searcher:
    def __init__(self, buggy_code_path_list, correct_code_path_list):
        self.k = 5
        self.__corr_code_map = get_dir_codes(correct_code_path_list)
        self.__buggy_code_map = get_dir_codes(buggy_code_path_list)
        self.__buggy_programs_map = get_programs_map(buggy_code_path_list)
        self.__correct_programs = get_programs(correct_code_path_list)
        self.__program_map = {}
        self.__match_ori_map = {}
        self.__gcr_time_map = {}
        self.run()

    # def cfs_search(self, rc_map, bug_code, bug_p):
    #     bug_func_map = get_func_map(bug_code)
    #     rc_list_map = {}
    #     for func_name, bug_func_code in bug_func_map.items():
    #         rc_list = rc_map.get(func_name)
    #         if rc_list is not None:
    #             if len(rc_list) != 0:
    #                 rc_list_map[func_name] = rc_list
    #                 continue
    #         rc_list = cfs_search_func(bug_p.get_method(func_name), self.__correct_programs)
    #         rc_list_map[func_name] = rc_list
    #     return rc_list_map

    def cfs_search(self, rc_map, bug_code, bug_p):
        bug_func_map = get_func_map(bug_code)
        rc_list_map = {}
        for func_name, bug_func_code in bug_func_map.items():
            rc_list = cfs_search_func(bug_p.get_method(func_name), self.__correct_programs)
            rc_list_map[func_name] = rc_list
        return rc_list_map

    def run(self):
        for bug_file_name, bug_code in self.__buggy_code_map.items():
            sel_corr_fn_code_list = list(self.__corr_code_map.items())
            sel_corr_code_list = [code for _, code in sel_corr_fn_code_list]
            if any(cfs_map_equal(get_cfs_map(bug_code),
                                 get_cfs_map(ori_corr_code))
                   for ori_corr_code in sel_corr_code_list):
                self.__match_ori_map[bug_file_name] = 1
            else:
                self.__match_ori_map[bug_file_name] = 0
            s_time = time.time()
            # corr_rc_map, first_result = first_search(bug_code, self.__corr_code_map)
            # if not first_result:
            corr_rc_map = self.cfs_search({}, bug_code, self.__buggy_programs_map.get(bug_file_name))
            func_map = astar_get_cls_rc(bug_code, corr_rc_map)
            search_time = float("%.4f" % (time.time() - s_time))
            self.__program_map[bug_file_name] = func_map
            self.__gcr_time_map[bug_file_name] = search_time

    def get_program_map(self):
        return self.__program_map

    def get_search_time_map(self):
        return self.__gcr_time_map

    def get_match_ori_map(self):
        return self.__match_ori_map

# class Searcher:
#     def __init__(self, buggy_code_path, correct_code_path_list):
#         self.k = 3
#         self.__buggy_program = get_program(buggy_code_path)
#         self.__correct_programs = get_programs(correct_code_path_list)
#         self.__program_maps = {}
#         self.run()
#
#     def run(self):
#         func_map = {}
#         search_time = 0
#         for func_name in self.__buggy_program.methods.keys():
#             k_th_closest_maps, s_time = search_kth_max_match(
#                 self.k, self.__buggy_program.get_method(func_name), self.__correct_programs)
#             func_map[func_name] = k_th_closest_maps
#             search_time += s_time
#         self.__program_maps = func_map
#
#     def get_program_maps(self):
#         return self.__program_maps

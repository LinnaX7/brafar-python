import re
import sys
import threading
import time
from timeout_decorator import timeout

from basic_framework.hole import Hole
from basic_framework.aligner import Aligner
from basic_framework.program_partition.block_builder import BlockNode, BlockBuilder, BlockType
from basic_framework.program_partition.method_builder import MethodBuilder
from basic_framework.program_partition.program_builder import ProgramBuilder, Reconstructor




@timeout(0.01)
def run_tc(code: str, input_path, output_path, __global_path):
    t_code = code
    if __global_path is not None:
        with open(__global_path, "r") as f:
            t_code += "\n" + f.read() + "\n"

    with open(input_path, "r") as f:
        t_code += "\n" + "result = " + f.read() + "\n"
        # exec_input = f.read() + "\n"

    with open(output_path, "r") as f:
        exp_output = eval(f.read().strip())
    loc = {}
    exec(t_code, loc)
    # print(loc['result'])
    return exp_output == loc['result']
    # print(loc['result'])


class TestResult:
    def __init__(self, code, input_path_folders, output_path_folders, __globals):
        self.__input_path_folders = input_path_folders
        self.__output_path_folders = output_path_folders
        self.__global_path = __globals
        self.__passed_input_path_folders = []
        self.__passed_output_path_folders = []
        self.__failed_input_path_folders = []
        self.__failed_output_path_folders = []
        self.__test_result = True
        self.__code = code
        self.validate(code)

    def get_code(self):
        return self.__code

    def get_test_result(self):
        return self.__test_result

    def get_failed_input_cases(self):
        return self.__failed_input_path_folders

    def get_failed_output_cases(self):
        return self.__failed_output_path_folders

    def validate(self, code):
        for i in range(len(self.__input_path_folders)):
            try:
                if not run_tc(code, self.__input_path_folders[i], self.__output_path_folders[i], self.__global_path):
                    # print(c_refactored_code)
                    self.__failed_input_path_folders.append(self.__input_path_folders[i])
                    self.__failed_output_path_folders.append(self.__output_path_folders[i])
                    self.__test_result = False
                else:
                    self.__passed_input_path_folders.append(self.__input_path_folders[i])
                    self.__passed_output_path_folders.append(self.__output_path_folders[i])
            except Exception as e:
                self.__failed_input_path_folders.append(self.__input_path_folders[i])
                self.__failed_output_path_folders.append(self.__output_path_folders[i])
                self.__test_result = False


# class TestThread(threading.Thread):
#     def __init__(self, runtime, code, test_case_input, test_case_output):
#         threading.Thread.__init__(self)
#         self.__runtime = runtime
#         self.__running = True
#         self.__code = code
#         self.__test_case_input = test_case_input
#         self.__test_case_output = test_case_output
#
#     def run(self):
#         def target_func():
#             sys.stdout = open("log.txt", "w")
#             run_tc(self.__code, self.__test_case_input, self.__test_case_output)
#             # test_001()
#             # search(1,1)
#             sys.stdout = sys.__stdout__
#
#         sub_thread = threading.Thread(target=target_func, args=())
#         sub_thread.daemon = True
#         sub_thread.start()
#         while not self.__running:
#             sub_thread.join(self.__runtime)
#
#     def stop(self):
#         self.__running = False


class ValuePair:
    def __init__(self, trace_index, in_value, out_value):
        self.__trace_index_in = trace_index
        self.__in_value = in_value
        self.__out_value = out_value

    def get_in_value(self):
        return self.__in_value

    def get_out_value(self):
        return self.__out_value

    def set_in_value(self, in_value):
        self.__in_value = in_value

    def set_out_value(self, out_value):
        self.__out_value = out_value

    def set_trace_index(self, trace_index):
        self.__trace_index_in = trace_index

    def get_trace_index(self):
        return self.__trace_index_in


class StackBuffer:
    def __init__(self, begin_in, end_in, test_trace, test_trace_log):
        self.__begin_in = begin_in
        self.__end_in = end_in
        self.__test_trace = test_trace
        self.__test_trace_log = test_trace_log

    def get_begin_in(self):
        return self.__begin_in

    def get_end_in(self):
        return self.__end_in

    def get_block_value(self, block_index):
        for i in range(self.__begin_in, self.__end_in):
            if self.__test_trace[i] == block_index:
                if (i * 2 + 1) < len(self.__test_trace_log):
                    return ValuePair(i, self.__test_trace_log[i * 2], self.__test_trace_log[i * 2 + 1])
                else:
                    return ValuePair(i, self.__test_trace_log[i * 2], None)
        return ValuePair(-1, None, None)

    def get_block_values(self, block_index):
        block_values = []
        for i in range(self.__begin_in, self.__end_in):
            if self.__test_trace[i] == block_index:
                if (i * 2 + 1) < len(self.__test_trace_log):
                    block_values.append(ValuePair(i, self.__test_trace_log[i * 2], self.__test_trace_log[i * 2 + 1]))
                else:
                    block_values.append(ValuePair(i, self.__test_trace_log[i * 2], None))
        return block_values

    def get_trace_by_index(self, t_index):
        if t_index >= self.__end_in:
            return None
        return self.__test_trace[t_index]

    def get_last_test_trace(self):
        if self.__end_in - 1 >= 0:
            return self.__test_trace[self.__end_in - 1]
        else:
            return -1


class Result:
    def __init__(self, need_recall, is_fault):
        self.__need_recall = need_recall
        self.__is_fault = is_fault
        self.__need_block_by_block_repair = False
        self.__need_repair_all = False

    def set_need_repair_all(self):
        self.__need_repair_all = True

    def get_need_repair_all(self):
        return self.__need_repair_all

    def set_need_recall(self, need_recall):
        self.__need_recall = need_recall

    def set_is_fault(self, is_fault):
        self.__is_fault = is_fault

    def set_need_b2b_repair(self):
        self.__need_block_by_block_repair = True

    def get_need_recall(self):
        return self.__need_recall

    def get_is_fault(self):
        return self.__is_fault

    def get_need_b2b_repair(self):
        return self.__need_block_by_block_repair


def get_children_values(block_nodes, children_blocks, stack_buffer: StackBuffer):
    block_values = []
    last_trace_block_index = stack_buffer.get_last_test_trace()
    # if last_trace_block_index < 0:
    #     print("sadad")
    for child in children_blocks:
        if child.get_type() == BlockType.BASIC_BLOCK:
            meta_index = child.get_meta_index()
            block_values.append(stack_buffer.get_block_value(meta_index))
        else:
            block_values.append(ValuePair(-1, None, None))
    for i in range(1, len(children_blocks) - 1):
        if children_blocks[i].get_type() != BlockType.BASIC_BLOCK:
            block_values[i] = ValuePair(-1, block_values[i - 1].get_out_value(), block_values[i + 1].get_in_value())
            if block_values[i + 1].get_in_value() is None:
                if children_blocks[i - 1].get_meta_index() < last_trace_block_index < \
                        children_blocks[i + 1].get_meta_index():
                    if block_nodes[last_trace_block_index].get_jump_block() is not None and \
                            block_nodes[last_trace_block_index].get_jump_block().get_type() == BlockType.CONTINUE:
                        block_values[i].set_out_value(
                            stack_buffer.get_block_value(last_trace_block_index).get_out_value())
    return block_values


def get_cond_value(block: BlockNode, block_stack: StackBuffer):
    __cond = block.get_children()[0]
    __body = block.get_children()[1]
    __body_begin_index = __body.get_children()[0].get_meta_index()
    __body_begin_value = block_stack.get_block_value(__body_begin_index)
    if __body_begin_value.get_trace_index() == -1:
        return False, __body_begin_value
    return True, __body_begin_value


class FaultLocator:
    def __init__(self, buggy_m, correct_m, correct_p: ProgramBuilder, failed_test_case_input, failed_test_case_output,
                 _aligner: Aligner, has_fixed, _global):
        self.__buggy_variable_trace_hole = Hole(buggy_m.get_m_node())
        self.__correct_variable_trace_hole = Hole(correct_m.get_m_node())
        self.__buggy_m: MethodBuilder = buggy_m
        self.__correct_m: MethodBuilder = correct_m
        self.__buggy_variable_trace_code = Reconstructor(
            correct_p.get_p_node(), self.__buggy_variable_trace_hole.get_m_node()).get_reconstructed_code()
        self.__correct_variable_trace_code = Reconstructor(
            correct_p.get_p_node(), self.__correct_variable_trace_hole.get_m_node()).get_reconstructed_code()
        self.__buggy_block_trace = []
        self.__correct_block_trace = []
        self.__buggy_block_trace_log = []
        self.__correct_block_trace_log = []
        self.__failed_test_case_input = failed_test_case_input
        self.__failed_test_case_output = failed_test_case_output
        self.__global_path = _global
        self.__aligner = _aligner
        self.__fault_block = None
        self.__test_result = None
        self.fault_localization()

    def get_correct_m(self):
        return self.__correct_m

    def get_correct_block_trace(self):
        return self.__correct_block_trace

    def get_fault_block(self):
        return self.__fault_block

    def get_test_result(self):
        return self.__test_result

    def construct_specification(self, target_m: MethodBuilder, target_code, test_trace, test_trace_log):
        # sys.stdout = open("log.txt", "w")
        # run_tc(self.__buggy_variable_trace_code, self.__failed_test_case_input, self.__failed_test_case_output)
        # sys.stdout = sys.__stdout__
        # print(target_code)
        # test_thread = TestThread(0.1, target_code, self.__failed_test_case_input, self.__failed_test_case_output)
        sys.stdout = open("log.txt", "w")
        try:
            run_tc(target_code, self.__failed_test_case_input, self.__failed_test_case_output, self.__global_path)
        finally:
            sys.stdout = sys.__stdout__
            # test_thread.start()
            # test_thread.join()
            # time.sleep(0.2)
            meta_blocks = target_m.get_meta_block_nodes()
            block_b: BlockBuilder = target_m.get_block_builder()
            with open("log.txt") as log_f:
                line = log_f.readline()
                while line:
                    if line.startswith("block"):
                        line = line.replace("\n", "")
                        index = re.findall(r"block\d+", line)
                        index = re.findall(r"\d+", index[0])
                        cur_block: BlockNode = meta_blocks[int(index[0])]
                        values = line[line.find(" ") + 1:]
                        # values = json.dumps(eval(values))
                        # data = json.loads(values)
                        try:
                            data = eval(values)
                            if len(test_trace_log) % 2 == 0:
                                test_trace.append(int(index[0]))
                            test_trace_log.append(data)
                        except:
                            return int(index[0]), False
                            # if cur_block.get_inValues() is not None:
                            #     if cur_block.get_outValues() is None or len(cur_block.get_inValues()) > len(
                            #             cur_block.get_outValues()):
                            #         cur_block.add_outValue(data)
                            #     else:
                            #         cur_block.add_inValue(data)
                            #         block_b.add_test_trace(int(index[0]))
                            #         test_trace.append(int(index[0]))
                            # else:
                            #     cur_block.add_inValue(data)
                            #     block_b.add_test_trace(int(index[0]))
                            #     test_trace.append(int(index[0]))
                    line = log_f.readline()
            return -1, True
        # block_b.init_specification()

    def fault_localization(self):
        self.construct_specification(self.__buggy_m, self.__buggy_variable_trace_code, self.__buggy_block_trace,
                                     self.__buggy_block_trace_log)
        index, c_c = self.construct_specification(self.__correct_m, self.__correct_variable_trace_code, self.__correct_block_trace,
                                     self.__correct_block_trace_log)
        buggy_stack = StackBuffer(0, len(self.__buggy_block_trace), self.__buggy_block_trace,
                                  self.__buggy_block_trace_log)
        correct_stack = StackBuffer(0, len(self.__correct_block_trace), self.__correct_block_trace,
                                    self.__correct_block_trace_log)
        self.fault_localization_body(self.__buggy_m.get_block_builder().get_root_block(),
                                     self.__correct_m.get_block_builder().get_root_block(), buggy_stack, correct_stack)
        if not c_c:
            if self.__fault_block is None:
                self.get_test_result().set_need_repair_all()
                return
            if self.__fault_block.get_meta_index() == index:
                self.get_test_result().set_need_repair_all()

    def fault_localization_body(self, buggy_body, correct_body, buggy_stack: StackBuffer, correct_stack: StackBuffer):
        buggy_children_block_values = get_children_values(self.__buggy_m.get_meta_block_nodes(),
                                                          buggy_body.get_children(), buggy_stack)
        correct_children_block_values = get_children_values(self.__correct_m.get_meta_block_nodes(),
                                                            correct_body.get_children(), correct_stack)
        for i in range(len(buggy_body.get_children())):
            cur_block: BlockNode = buggy_body.get_children()[i]
            block_test_result = self.is_block_has_fault(cur_block, buggy_children_block_values[i],
                                                        correct_children_block_values[i])
            if block_test_result.get_is_fault() or block_test_result.get_need_recall():
                fault_block = None
                cur_index = i
                if block_test_result.get_is_fault():
                    fault_block = cur_block
                elif block_test_result.get_need_recall():
                    if i > 0:
                        fault_block = buggy_body.get_children()[i - 1]
                        cur_index = i - 1
                if fault_block is not None:
                    if fault_block.get_type() == BlockType.BASIC_BLOCK:
                        self.__fault_block = fault_block
                        self.__test_result = block_test_result
                        break
                    buggy_block_begin_in = (buggy_children_block_values[cur_index - 1].get_trace_index() + 1)
                    buggy_block_end_in = buggy_children_block_values[cur_index + 1].get_trace_index()
                    if buggy_block_end_in < 0:
                        buggy_block_end_in = buggy_stack.get_end_in()
                    buggy_block_stack_buffer = StackBuffer(buggy_block_begin_in, buggy_block_end_in,
                                                           self.__buggy_block_trace, self.__buggy_block_trace_log)
                    correct_block_begin_in = (correct_children_block_values[cur_index - 1].get_trace_index() + 1)
                    correct_block_end_in = correct_children_block_values[cur_index + 1].get_trace_index()
                    if correct_block_end_in < 0:
                        correct_block_end_in = correct_stack.get_end_in()
                    correct_block_stack_buffer = StackBuffer(correct_block_begin_in, correct_block_end_in,
                                                             self.__correct_block_trace, self.__correct_block_trace_log)
                    if fault_block.get_type() == BlockType.IF_BLOCK:
                        self.fault_localization_If(fault_block, buggy_children_block_values[cur_index],
                                                   correct_children_block_values[cur_index], buggy_block_stack_buffer,
                                                   correct_block_stack_buffer)
                        break
                    if fault_block.get_type() == BlockType.WHILE_BLOCK:
                        self.fault_localization_WhileFor(fault_block, buggy_children_block_values[cur_index],
                                                         correct_children_block_values[cur_index],
                                                         buggy_block_stack_buffer, correct_block_stack_buffer)
                        break
                    if fault_block.get_type() == BlockType.FOREACH_BLOCK:
                        self.fault_localization_WhileFor(fault_block, buggy_children_block_values[cur_index],
                                                         correct_children_block_values[cur_index],
                                                         buggy_block_stack_buffer, correct_block_stack_buffer)
                        break

    def fault_localization_If(self, b_block: BlockNode, b_specification: ValuePair, c_specification: ValuePair,
                              buggy_stack: StackBuffer, correct_stack: StackBuffer):
        c_block = self.__aligner.get_block_map().get(b_block)
        b_cond = b_block.get_children()[0]
        b_body: BlockNode = b_block.get_children()[1]
        c_body: BlockNode = c_block.get_children()[1]
        b_cond_value, b_body_begin_value = get_cond_value(b_block, buggy_stack)
        c_cond_value, c_body_begin_value = get_cond_value(c_block, correct_stack)
        if b_cond_value != c_cond_value:
            self.__fault_block = b_cond
            return
        if b_cond_value:
            test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_specification.get_in_value(),
                                                                    b_body_begin_value.get_in_value()),
                                                  ValuePair(-1, c_specification.get_in_value(),
                                                            c_body_begin_value.get_in_value()))
            if test_result.get_is_fault():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
            elif test_result.get_need_b2b_repair():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
            self.fault_localization_body(b_body, c_body, buggy_stack, correct_stack)
        else:
            if len(b_block.get_children()) == 3:
                b_else = b_block.get_children()[2]
                c_else = c_block.get_children()[2]
                b_body_begin_value = buggy_stack.get_block_value(b_else.get_children()[0].get_meta_index())
                c_body_begin_value = correct_stack.get_block_value(c_else.get_children()[0].get_meta_index())
                test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_specification.get_in_value(),
                                                                        b_body_begin_value.get_in_value()),
                                                      ValuePair(-1, c_specification.get_in_value(),
                                                                c_body_begin_value.get_in_value()))
                if test_result.get_is_fault():
                    self.__fault_block = b_cond
                    self.__test_result = test_result
                    return
                elif test_result.get_need_b2b_repair():
                    self.__fault_block = b_cond
                    self.__test_result = test_result
                    return
                self.fault_localization_body(b_else, c_else, buggy_stack, correct_stack)
            else:
                test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_specification.get_in_value(),
                                                                        b_specification.get_out_value()),
                                                      ValuePair(-1, c_specification.get_in_value(),
                                                                c_specification.get_out_value()))
                if test_result.get_is_fault():
                    self.__fault_block = b_cond
                    self.__test_result = test_result
                    return
                elif test_result.get_need_b2b_repair():
                    self.__fault_block = b_cond
                    self.__test_result = test_result
                    return

    def fault_localization_WhileFor(self, b_block: BlockNode, b_specification: ValuePair, c_specification: ValuePair,
                                    buggy_stack: StackBuffer, correct_stack: StackBuffer):
        c_block = self.__aligner.get_block_map().get(b_block)
        b_body = b_block.get_children()[1]
        c_body = c_block.get_children()[1]
        b_body_index = b_body.get_children()[0].get_meta_index()
        c_body_index = c_body.get_children()[0].get_meta_index()
        b_body_values = buggy_stack.get_block_values(b_body_index)
        c_body_values = correct_stack.get_block_values(c_body_index)
        b_cond = b_block.get_children()[0]
        if len(b_body_values) != 0 and len(c_body_values) != 0:
            test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_specification.get_in_value(),
                                                                    b_body_values[0].get_in_value()),
                                                  ValuePair(-1, c_specification.get_in_value(),
                                                            c_body_values[0].get_in_value()))
            if test_result.get_is_fault():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
            elif test_result.get_need_b2b_repair():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
        a = min(len(b_body_values), len(c_body_values))
        for i in range(a - 1):
            b_body_stack = StackBuffer(b_body_values[i].get_trace_index(), b_body_values[i + 1].get_trace_index(),
                                       self.__buggy_block_trace, self.__buggy_block_trace_log)
            c_body_stack = StackBuffer(c_body_values[i].get_trace_index(), c_body_values[i + 1].get_trace_index(),
                                       self.__correct_block_trace, self.__correct_block_trace_log)
            self.fault_localization_body(b_body, c_body, b_body_stack, c_body_stack)
            if self.__fault_block is not None:
                return
            test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_body_values[i].get_out_value(),
                                                                    b_body_values[i + 1].get_in_value()),
                                                  ValuePair(-1, c_body_values[i].get_out_value(),
                                                            c_body_values[i + 1].get_in_value()))
            if test_result.get_is_fault():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
            elif test_result.get_need_b2b_repair():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
        if len(b_body_values) == 0 and len(c_body_values) == 0:
            test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_specification.get_in_value(),
                                                                    b_specification.get_out_value()),
                                                  ValuePair(-1, c_specification.get_in_value(),
                                                            c_specification.get_out_value()))
            if test_result.get_is_fault():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
            elif test_result.get_need_b2b_repair():
                self.__fault_block = b_cond
                self.__test_result = test_result
                return
        else:
            if len(b_body_values) == len(c_body_values):
                b_body_stack = StackBuffer(b_body_values[a - 1].get_trace_index(), buggy_stack.get_end_in(),
                                           self.__buggy_block_trace, self.__buggy_block_trace_log)
                c_body_stack = StackBuffer(c_body_values[a - 1].get_trace_index(), correct_stack.get_end_in(),
                                           self.__correct_block_trace, self.__correct_block_trace_log)
                self.fault_localization_body(b_body, c_body, b_body_stack, c_body_stack)
                if self.__fault_block is not None:
                    return
                self.__fault_block = b_block.get_children()[0]
            elif len(b_body_values) == 0 or len(c_body_values) == 0:
                if len(b_body_values) == 0 and len(c_body_values) != 0:
                    test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_specification.get_in_value(),
                                                                            b_specification.get_out_value()),
                                                          ValuePair(-1, c_specification.get_in_value(),
                                                                    c_body_values[0].get_in_value()))
                else:
                    test_result = self.is_block_has_fault(b_cond, ValuePair(-1, b_specification.get_in_value(),
                                                                            b_body_values[0].get_in_value()),
                                                          ValuePair(-1, c_specification.get_in_value(),
                                                                    c_specification.get_out_value()))
                if test_result.get_need_b2b_repair():
                    self.__fault_block = b_cond
                    self.__test_result = test_result
                    return
                else:
                    test_result.set_is_fault(True)
                    self.__fault_block = b_cond
                    self.__test_result = test_result
                    return
            else:
                if len(b_body_values) > len(c_body_values):
                    b_body_stack = StackBuffer(b_body_values[a - 1].get_trace_index(),
                                               b_body_values[a].get_trace_index(),
                                               self.__buggy_block_trace, self.__buggy_block_trace_log)
                    c_body_stack = StackBuffer(c_body_values[a - 1].get_trace_index(), correct_stack.get_end_in(),
                                               self.__correct_block_trace, self.__correct_block_trace_log)
                    self.fault_localization_body(b_body, c_body, b_body_stack, c_body_stack)
                    if self.__fault_block is not None:
                        return
                    self.__fault_block = b_block.get_children()[0]
                else:
                    b_body_stack = StackBuffer(b_body_values[a - 1].get_trace_index(), buggy_stack.get_end_in(),
                                               self.__buggy_block_trace, self.__buggy_block_trace_log)
                    c_body_stack = StackBuffer(c_body_values[a - 1].get_trace_index(),
                                               c_body_values[a].get_trace_index(),
                                               self.__correct_block_trace, self.__correct_block_trace_log)
                    self.fault_localization_body(b_body, c_body, b_body_stack, c_body_stack)
                    if self.__fault_block is not None:
                        return
                    self.__fault_block = b_block.get_children()[0]

    def is_block_has_fault(self, cur_block_node, buggy_block_specification: ValuePair,
                           correct_block_specification: ValuePair):
        test_result = Result(False, False)
        related_correct_block_node = self.__aligner.get_block_map().get(cur_block_node)
        variable_map = self.__aligner.get_variable_map_12()
        variable_map_21 = self.__aligner.get_variable_map_21()
        buggy_in_values = buggy_block_specification.get_in_value()
        buggy_out_values = buggy_block_specification.get_out_value()
        correct_in_values = correct_block_specification.get_in_value()
        correct_out_values = correct_block_specification.get_out_value()
        if buggy_in_values is None and correct_in_values is not None:
            test_result.set_need_recall(True)
            return test_result
        if buggy_in_values is not None and correct_in_values is None:
            test_result.set_need_recall(True)
            return test_result
        if buggy_in_values is None and correct_in_values is None:
            # test_result.set_need_recall(True)
            return test_result
        doubt_vars = []
        for var in buggy_in_values.keys():
            if variable_map.get(var) is None:
                test_result.set_need_recall(True)
                return test_result
            co_var = variable_map.get(var)
            if correct_in_values.get(co_var) is None:
                doubt_vars.append(var)
            else:
                if buggy_in_values.get(var) != correct_in_values.get(co_var):
                    test_result.set_need_recall(True)
                    return test_result

        if buggy_out_values is None and correct_out_values is not None:
            if len(doubt_vars) != 0:
                test_result.set_need_recall(True)
                return test_result
            test_result.set_is_fault(True)
            return test_result
        if buggy_out_values is not None and correct_out_values is None:
            if len(doubt_vars) != 0:
                test_result.set_need_recall(True)
                return test_result
            test_result.set_is_fault(True)
            return test_result
        if buggy_out_values is None and correct_out_values is None:
            if len(doubt_vars) != 0:
                test_result.set_need_recall(True)
                return test_result
            test_result.set_is_fault(True)
            return test_result
        for var in doubt_vars:
            co_var = variable_map.get(var)
            if buggy_out_values.get(var) != correct_out_values.get(co_var):
                test_result.set_need_recall(True)
                test_result.set_need_b2b_repair()
                return test_result
        for var in buggy_out_values.keys():
            if variable_map.get(var) is None:
                test_result.set_is_fault(True)
                test_result.set_need_b2b_repair()
                return test_result
            co_var = variable_map.get(var)
            if correct_out_values.get(co_var) is None:
                continue
            if buggy_out_values.get(var) != correct_out_values.get(co_var):
                test_result.set_is_fault(True)
        for var in correct_out_values.keys():
            if variable_map_21.get(var) is not None:
                b_var = variable_map_21.get(var)
                if buggy_out_values.get(b_var) is None:
                    test_result.set_is_fault(True)
        if cur_block_node.get_jump_block() is None and related_correct_block_node.get_jump_block() is not None:
            test_result.set_is_fault(True)
        if cur_block_node.get_jump_block() is not None and related_correct_block_node.get_jump_block() is None:
            test_result.set_is_fault(True)
        if cur_block_node.get_jump_block() is not None and related_correct_block_node.get_jump_block() is not None:
            if cur_block_node.get_jump_block().get_type() != related_correct_block_node.get_jump_block().get_type():
                test_result.set_is_fault(True)
            if cur_block_node.get_jump_block().get_type() == BlockType.RETURN:
                test_result.set_is_fault(True)
        return test_result

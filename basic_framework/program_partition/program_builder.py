import ast
import copy
from _ast import Module

from basic_framework.program_partition import method_builder
from basic_framework.hole import Hole


def syntax_check(code):
    try:
        cm = compile(code, "<string>", "exec")
        return cm
    except:
        print("syntax error")
        return None


def is_m_match(m1: method_builder.MethodBuilder, m2: method_builder.MethodBuilder):
    if m1.cfs == m2.cfs:
        return True
    return False


class ProgramBuilder(ast.NodeVisitor):
    def __init__(self, code: str, f_name):
        self.f_name = f_name
        self.code = code
        self.p_node = ast.parse(code)
        self.methods = {}
        self.visit(self.p_node)
        self.lines = code.count("\n")
        for method_b in self.methods.values():
            method_b.init_()

    def get_f_name(self):
        return self.f_name

    def get_b_funcs(self):
        return self.methods.keys()

    def visit_Module(self, node: Module):
        i = 0
        while i < len(node.body):
            cur_node = node.body[i]
            if not isinstance(cur_node, ast.FunctionDef):
                node.body.remove(cur_node)
            else:
                i+=1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.methods[node.name] = method_builder.MethodBuilder(node, self)
        # new_m_node = Refactoring().visit(node)
        # self.methods[node.name] = method_builder.MethodBuilder(new_m_node)

    def get_method(self, m_name):
        return self.methods.get(m_name)

    def get_p_node(self):
        return self.p_node


class Reconstructor(ast.NodeVisitor):
    def __init__(self, p_node, m_node):
        self.__m_node = m_node
        self.__p_node = copy.deepcopy(p_node)
        self.visit(self.__p_node)

    def visit_Module(self, node: Module):
        for i in range(len(node.body)):
            cur_node = node.body[i]
            if isinstance(cur_node, ast.FunctionDef):
                if cur_node.name == self.__m_node.name:
                    node.body[i] = self.__m_node
        return node

    # def visit_FunctionDef(self, node):
    #     if node.name == self.__m_node.name:
    #         node = self.__m_node
    #         return node

    def get_reconstructed_p_node(self):
        return self.__p_node

    def get_reconstructed_code(self):
        return ast.unparse(self.__p_node)


def is_p_match(p1: ProgramBuilder, p2: ProgramBuilder):
    if p1 is None or p2 is None:
        return False
    for key in p1.methods.keys():
        if key in p2.methods.keys():
            if not is_m_match(p1.methods.get(key), p2.methods.get(key)):
                return False
        else:
            return False
    return True


def is_p_match_m(p1: ProgramBuilder, p2: ProgramBuilder, method_name):
    if p1 is None or p2 is None:
        return False
    if method_name in p1.methods.keys() and method_name in p2.methods.keys():
        if not is_m_match(p1.methods.get(method_name), p2.methods.get(method_name)):
            return False
        else:
            return True
    return True


def get_program_from_code(code, f_name):
    cm = syntax_check(code)
    # exec(cm)
    # type(cm)
    if cm is not None:
        p = ProgramBuilder(code, f_name)
        return p
    return None


def get_program(file):
    code = ""
    with open(file, "r") as f:
        code += f.read()
    # print(file)
    p = get_program_from_code(code, file)
    return p


def get_code(file):
    code = ""
    with open(file, "r") as f:
        code += f.read()
    return code


def get_programs(files):
    programs = []
    for file in files:
        p = get_program(file)
        if p is not None:
            programs.append(p)
    return programs


def get_programs_map(files):
    programs_map = {}
    for file in files:
        p = get_program(file)
        if p is not None:
            programs_map[file] = p
    return programs_map

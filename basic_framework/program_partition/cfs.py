import ast

import astunparse
from fastcache import clru_cache

from basic_framework.program_partition.utils import regularize
from basic_framework.program_partition.statement import *



@clru_cache(maxsize=1024)
def get_cfs_map(code):
    func_map = get_func_map(code)

    cfs_map = {}
    for func_name, func_code in func_map.items():
        bb_list, stru_list, indent_list = get_func_cfs(func_code)
        cfs_map[func_name] = (bb_list, stru_list, indent_list)
    return cfs_map


def cfs_map_equal(cfs_map_a, cfs_map_b):
    if set(cfs_map_a.keys()) != set(cfs_map_b.keys()):
        return False

    for cfs_func in cfs_map_a.keys():
        _, stru_list_a, indent_list_a = cfs_map_a[cfs_func]
        _, stru_list_b, indent_list_b = cfs_map_b[cfs_func]
        if stru_list_a != stru_list_b or \
                indent_list_a != indent_list_b:
            return False
    return True


def get_func_map(code):

    class FuncVisitor(ast.NodeVisitor):
        def __init__(self):
            super()
            self.func_map = {}

        def visit_FunctionDef(self, node):
            self.func_map[node.name] = regularize(astunparse.unparse(node))

        def run(self, code):
            n = ast.parse(code)
            self.visit(n)
            return self.func_map

    return FuncVisitor().run(code)


def get_func_cfs(code):
    line_list = code.split("\n")
    block_list = []
    stru_list = []
    indent_list = []
    block_code = ""

    curr_ind = 0
    for line in line_list:
        if "empty_hole" in line or len(line) == 0:
            continue
        if is_method_sign(line):
            block_code = ""
            block_list.append(line + "\n")
            stru_list.append('sig')
            indent_list.append(curr_ind)
            curr_ind += 4
        elif is_if_stat(line):
            block_list.append(block_code)
            stru_list.append('bb')
            indent_list.append(curr_ind)

            line_ind = get_indent(line)
            if curr_ind < line_ind:
                block_list.append("")
                stru_list.append("bb")
                indent_list.append(line_ind)
            elif curr_ind > line_ind:
                for k in range(curr_ind - 4, line_ind - 4, -4):
                    block_list.append("")
                    stru_list.append("bb")
                    indent_list.append(k)

            block_code = ""
            block_list.append(line + "\n")
            stru_list.append('if')
            indent_list.append(line_ind)
            curr_ind = line_ind + 4
        elif is_elif_stat(line):
            block_list.append(block_code)
            stru_list.append('bb')
            indent_list.append(curr_ind)

            line_ind = get_indent(line)
            if curr_ind > line_ind:
                for k in range(curr_ind - 4, line_ind, -4):
                    block_list.append("")
                    stru_list.append("bb")
                    indent_list.append(k)

            block_code = ""
            block_list.append(line + "\n")
            stru_list.append('elif')
            indent_list.append(get_indent(line))
            curr_ind = get_indent(line) + 4
        elif is_else_stat(line):
            block_list.append(block_code)
            stru_list.append('bb')
            indent_list.append(curr_ind)

            line_ind = get_indent(line)
            if curr_ind > line_ind:
                for k in range(curr_ind - 4, line_ind, -4):
                    block_list.append("")
                    stru_list.append("bb")
                    indent_list.append(k)

            block_code = ""
            block_list.append(line + "\n")
            stru_list.append('else')
            indent_list.append(get_indent(line))
            curr_ind = get_indent(line) + 4
        elif is_for_loop_stat(line):
            block_list.append(block_code)
            stru_list.append('bb')
            indent_list.append(curr_ind)

            line_ind = get_indent(line)
            if curr_ind < line_ind:
                block_list.append("")
                stru_list.append("bb")
                indent_list.append(line_ind)
            elif curr_ind > line_ind:
                for k in range(curr_ind - 4, line_ind - 4, -4):
                    block_list.append("")
                    stru_list.append("bb")
                    indent_list.append(k)

            block_code = ""
            block_list.append(line + "\n")
            stru_list.append('for')
            indent_list.append(line_ind)
            curr_ind = line_ind + 4
        elif is_while_loop_stat(line):
            block_list.append(block_code)
            stru_list.append('bb')
            indent_list.append(curr_ind)

            line_ind = get_indent(line)
            if curr_ind < line_ind:
                block_list.append("")
                stru_list.append("bb")
                indent_list.append(line_ind)
            elif curr_ind > line_ind:
                for k in range(curr_ind - 4, line_ind - 4, -4):
                    block_list.append("")
                    stru_list.append("bb")
                    indent_list.append(k)

            block_code = ""
            block_list.append(line + "\n")
            stru_list.append('while')
            indent_list.append(line_ind)
            curr_ind = line_ind + 4
        else:
            ind = get_indent(line)
            if ind == curr_ind:
                block_code += line + "\n"
            elif ind > curr_ind:
                for tmp_ind in range(curr_ind, ind, 4):
                    block_list.append(block_code)
                    stru_list.append('bb')
                    indent_list.append(tmp_ind)
                    block_code = ""
                block_code = line + "\n"
                curr_ind = ind
            else:
                for tmp_ind in range(curr_ind, ind, -4):
                    block_list.append(block_code)
                    stru_list.append('bb')
                    indent_list.append(tmp_ind)
                    block_code = ""
                block_code = line + "\n"
                curr_ind = ind
    if len(block_code) > 0:
        block_list.append(block_code)
        stru_list.append('bb')
        curr_ind = get_indent(block_code.split("\n")[0])
        indent_list.append(curr_ind)
        block_code = ""
        if curr_ind > 4:
            for ind in range(curr_ind - 4, 0, -4):
                block_list.append(block_code)
                block_code = ""
                stru_list.append('bb')
                indent_list.append(ind)

    assert (len(block_list) == len(stru_list) and
            len(block_list) == len(indent_list))
    return block_list, stru_list, indent_list


if __name__ == '__main__':
    print(get_func_cfs("def search(x, seq):\n\tfor i, elem in enumerate(seq):\n\t\tif x <= elem:\n\t\t\treturn i\n\treturn len(seq)"))

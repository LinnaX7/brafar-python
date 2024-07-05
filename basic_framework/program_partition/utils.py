
import ast
import astunparse
from basic_framework.program_partition.statement import *



def regularize(code):
    '''change code style (tab to space)'''
    # remove comment
    code = astunparse.unparse(ast.parse(code))

    # put logical lines into one physical line
    token_list = get_token_list(code)

    new_code = ""
    tmp_list = []
    indent_str = ""

    new_line_flag = False
    for token in token_list:
        if tok_name[token.exact_type] in ["NEWLINE", "ENDMARKER"]:
            new_code += indent_str + " ".join([tmp_token.string for tmp_token in tmp_list]) + "\n"
            tmp_list = []
            new_line_flag = True
        elif tok_name[token.exact_type] == "NL":
            pass
        elif tok_name[token.exact_type] == "COMMENT":
            pass
        elif tok_name[token.exact_type] == "INDENT":
            indent_str += "    "
        elif tok_name[token.exact_type] == "DEDENT":
            if new_line_flag:
                indent_str = indent_str[:-4]
        else:
            new_line_flag = False
            tmp_list.append(token)

    final_code = ""
    for line in new_code.split("\n"):

        token_list = get_token_list(line)
        if any([token.string in ["from", "import"] for token in token_list]):
            pass
        else:
            if get_indent(line) == 0 and \
                len(token_list) > 1 and \
                    all([token.string != "def" for token in token_list]):
                pass
            else:
                final_code += line + "\n"

    return final_code

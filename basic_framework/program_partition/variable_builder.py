import ast
from _ast import FunctionDef, Name, expr
from typing import Any


class Variable:
    def __init__(self, name, node):
        self.__uses = None
        self.__return_uses = None
        self.__name = name
        self.__def = -1
        self.__uses: set
        self.__type = None
        self.__return_uses: set
        self.__define_node = node
        self.__def_use_mark = 0
        self.__in_value = []
        self.__out_value = []
        self.init_type()

    def get_type(self):
        return self.__type

    def init_type(self):
        if isinstance(self.__define_node, ast.Assign):
            if isinstance(self.__define_node.value, ast.List):
                self.__type = "List"
            elif isinstance(self.__define_node.value, ast.Constant):
                vss = self.__define_node.value.value
                self.__type = str(type(vss))

    def add_def_use_mark(self, mark):
        self.__def_use_mark += mark

    def set_def(self, index):
        self.__def = index

    def get_def(self):
        return self.__def

    def set_def_node(self, def_node):
        self.__define_node = def_node

    def get_uses(self):
        return self.__uses

    def get_return_uses(self):
        return self.__return_uses

    def get_def_use_mark(self):
        return self.__def_use_mark

    def add_def_use(self, index, mark):
        if self.__uses is None:
            li = [index]
            self.__uses = set(li)
            self.add_def_use_mark(mark)
        else:
            if self.__uses.__contains__(index):
                return
            self.__uses.add(index)
            self.add_def_use_mark(mark)

    def add_return_use(self, index, mark):
        if self.__return_uses is None:
            li = [index]
            self.__return_uses = set(li)
            self.add_def_use_mark(mark)
        else:
            if self.__return_uses.__contains__(index):
                return
            self.__return_uses.add(index)
            self.add_def_use_mark(mark)

    def get_name(self):
        return self.__name


class VariableBuilder(ast.NodeVisitor):
    def __init__(self, m_node):
        self.__variable_list = []
        self.__variable_map = {}
        self.__param_list = []
        self.__param_size = 0
        self.__ret_variables = []
        self.init_variable_list(m_node)

    def get_param_list(self):
        return self.__param_list

    def get_variable_list(self):
        return self.__variable_list

    def init_variable_list(self, m_node):
        self.visit(m_node)

    def add_ret_var(self, var):
        self.__ret_variables.append(var)

    def get_ret_vars(self):
        return self.__ret_variables

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        for par in node.args.args:
            var = Variable(par.arg, par)
            self.__param_list.append(var)
            self.__variable_list.append(var)
            self.__variable_map[par.arg] = var
        for node in ast.walk(node):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if self.__variable_map.get(node.id) is None:
                    var = Variable(node.id, node)
                    var.set_def_node(node)
                    self.__variable_list.append(var)
                    self.__variable_map[node.id] = var

    def set_variable_DU(self, variable_name, def_use_id, mark):
        var = self.__variable_map.get(variable_name)
        if var is not None:
            var.add_def_use(def_use_id, mark)

    def set_variable_Define(self, variable_name, def_index):
        var = self.__variable_map.get(variable_name)
        if var is not None:
            if var.get_def() == -1:
                var.set_def(def_index)

    def set_variable_return_use(self, variable_name, def_use_id, mark):
        var = self.__variable_map.get(variable_name)
        if var is not None:
            var.add_return_use(def_use_id, mark)
            self.add_ret_var(var)

    def get_variable_by_name(self, name):
        return self.__variable_map.get(name)

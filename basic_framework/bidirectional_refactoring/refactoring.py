import ast


class Refactoring(ast.NodeTransformer):
    def __init__(self, m_node):
        self.__m_node = m_node
        self.visit(self.__m_node)

    def visit(self, node):
        # self.generic_visit(node)
        if isinstance(node, ast.FunctionDef) or (
                isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                             isinstance(node, ast.While))):
            i = 0
            while i < len(node.body):
                if isinstance(node, ast.FunctionDef) or (
                        isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                                     isinstance(node, ast.While))):
                    self.visit(node.body[i])
                cur_node = node.body[i]
                if isinstance(cur_node, ast.If):
                    flag = False
                    # print(ast.unparse(node.body[i]))

                    for st in cur_node.body:
                        if type(st) == ast.Return or (type(st) == ast.Break or type(st) == ast.Continue):
                            flag = True
                            break
                    if flag:
                        t = i
                        for st in cur_node.orelse:
                            node.body.insert(t + 1, st)
                            t += 1
                        cur_node.orelse.clear()
                    j = 0
                    while j < len(cur_node.orelse):
                        self.visit(cur_node.orelse[j])
                        cur_cur_node = cur_node.orelse[j]
                        if isinstance(cur_cur_node, ast.If):
                            flag = False
                            # print(ast.unparse(node.body[i]))
                            for st in cur_cur_node.body:
                                if type(st) == ast.Return or (type(st) == ast.Break or type(st) == ast.Continue):
                                    flag = True
                                    break
                            if flag:
                                t = j
                                for st in cur_cur_node.orelse:
                                    cur_node.orelse.insert(t + 1, st)
                                    t += 1
                                cur_cur_node.orelse.clear()
                        j += 1
                i += 1
        return node


class InitialRefactor(ast.NodeTransformer):
    def __init__(self, m_node):
        self.__m_node = m_node
        self.visit(self.__m_node)

    def visit(self, node):
        if isinstance(node, ast.FunctionDef) or (
                isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                             isinstance(node, ast.While))):
            i = 0
            while i < len(node.body):
                if isinstance(node, ast.FunctionDef) or (
                        isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                                     isinstance(node, ast.While))):
                    self.visit(node.body[i])
                cur_node = node.body[i]
                if isinstance(cur_node, ast.For) or isinstance(cur_node, ast.While):
                    if len(cur_node.orelse) != 0:
                        t = i
                        for st in cur_node.orelse:
                            node.body.insert(t + 1, st)
                            t += 1
                        cur_node.orelse.clear()
                i += 1
        if isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                             isinstance(node, ast.While)):
            if len(node.orelse) != 0:
                i = 0
                while i < len(node.orelse):
                    if isinstance(node, ast.FunctionDef) or (
                            isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                                         isinstance(node, ast.While))):
                        self.visit(node.orelse[i])
                    cur_node = node.orelse[i]
                    if isinstance(cur_node, ast.For) or isinstance(cur_node, ast.While):
                        if len(cur_node.orelse) != 0:
                            t = i
                            for st in cur_node.orelse:
                                node.orelse.insert(t + 1, st)
                                t += 1
                            cur_node.orelse.clear()
                    i += 1


class BranchChanging(ast.NodeTransformer):
    def __init__(self, if_nodes):
        self.if_nodes = if_nodes

    def visit_If(self, node: ast.If):
        if node in self.if_nodes:
            if isinstance(node.test, ast.Constant) and node.test.value:
                node.test.value = False
            elif isinstance(node.test, ast.Constant) and not node.test.value:
                node.test.value = True
            else:
                node.test = ast.UnaryOp(ast.Not(), node.test)
            temp = []
            for st in node.body:
                temp.append(st)
            if node.orelse is []:
                node.body = ast.Pass
            else:
                node.body = node.orelse
            node.orelse = temp
        self.generic_visit(node)
        return node


class ConditionChanging(ast.NodeTransformer):
    def __init__(self, if_node):
        self.if_node = if_node

    def visit_If(self, node: ast.If):
        if node is self.if_node:
            if isinstance(node.test, ast.Constant) and node.test.value:
                node.test.value = False
            elif isinstance(node.test, ast.Constant) and not node.test.value:
                node.test.value = True
            else:
                node.test = ast.UnaryOp(ast.Not(), node.test)
        self.generic_visit(node)
        return node


class Recover(ast.NodeTransformer):
    def __init__(self, m_node):
        self.__m_node = m_node
        self.visit(self.__m_node)

    def visit(self, node):
        if isinstance(node, ast.FunctionDef) or (
                isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                             isinstance(node, ast.While))):
            i = 0
            while i < len(node.body):
                flag = False
                if isinstance(node, ast.FunctionDef) or (
                        isinstance(node, ast.If) or (isinstance(node, ast.For) or
                                                     isinstance(node, ast.While))):
                    self.visit(node.body[i])
                cur_node = node.body[i]
                if isinstance(cur_node, ast.FunctionDef) or (
                        isinstance(cur_node, ast.If) or (isinstance(cur_node, ast.For) or
                                                     isinstance(cur_node, ast.While))):
                    if len(cur_node.body) == 0 and len(cur_node.orelse) == 0:
                        flag = True
                        node.body.remove(cur_node)
                        continue
                if isinstance(cur_node, ast.If):
                    if isinstance(cur_node.test, ast.Constant) and cur_node.test.value:
                        t = i
                        node.body.remove(cur_node)
                        flag = True
                        for st in cur_node.body:
                            if not isinstance(st, ast.Pass):
                                node.body.insert(t, st)
                                t += 1
                    elif isinstance(cur_node.test, ast.Constant) and not cur_node.test.value:
                        node.body.remove(cur_node)
                        flag = True
                        if len(cur_node.orelse) != 0:
                            t = i
                            for st in cur_node.orelse:
                                if not isinstance(st, ast.Pass):
                                    node.body.insert(t, st)
                                    t += 1
                elif isinstance(cur_node, ast.Pass):
                    if len(node.body) > 1:
                        node.body.remove(cur_node)
                        flag = True
                if not flag:
                    i += 1
        if isinstance(node, ast.If):
            if len(node.orelse) != 0 :
                i = 0
                while i < len(node.orelse):
                    flag = False

                    self.visit(node.orelse[i])
                    cur_node = node.orelse[i]
                    if isinstance(cur_node, ast.FunctionDef) or (
                            isinstance(cur_node, ast.If) or (isinstance(cur_node, ast.For) or
                                                             isinstance(cur_node, ast.While))):
                        if len(cur_node.body) == 0:
                            flag = True
                            node.orelse.remove(cur_node)
                            continue
                    if isinstance(cur_node, ast.If):
                        if isinstance(cur_node.test, ast.Constant) and cur_node.test.value:
                            t = i
                            node.orelse.remove(cur_node)
                            flag = True
                            for st in cur_node.body:
                                if not isinstance(st, ast.Pass):
                                    node.orelse.insert(t, st)
                                    t += 1
                        elif isinstance(cur_node.test, ast.Constant) and not cur_node.test.value:
                            node.orelse.remove(cur_node)
                            flag = True
                            if len(cur_node.orelse) != 0:
                                t = i
                                for st in cur_node.orelse:
                                    if not isinstance(st, ast.Pass):
                                        node.orelse.insert(t, st)
                                        t += 1
                    elif isinstance(cur_node, ast.Pass):
                        node.orelse.remove(cur_node)
                        flag = True
                    if not flag:
                        i += 1

        return node


if __name__ == '__main__':
    print(ast.dump(ast.parse("if True:"
                             "  pass")))


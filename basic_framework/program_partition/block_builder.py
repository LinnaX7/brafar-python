import ast
from _ast import For, While, If
from enum import Enum
from typing import Any


class BlockType(Enum):
    METHOD_ENTRY = 0
    IF_BLOCK = 1
    IF_COND = 2
    IF_BODY = 3
    ELSE_BODY = 4
    WHILE_BLOCK = 5
    WHILE_COND = 6
    WHILE_BODY = 7
    FOREACH_BLOCK = 8
    FOREACH_ITER = 9
    FOREACH_BODY = 10
    RETURN = 11
    BREAK = 12
    CONTINUE = 13
    BASIC_BLOCK = 14


def get_block_type(st):
    block_type = -1
    if type(st) == ast.If:
        block_type = BlockType.IF_BLOCK
    elif type(st) == ast.For:
        block_type = BlockType.FOREACH_BLOCK
    elif type(st) == ast.While:
        block_type = BlockType.WHILE_BLOCK
    return block_type


def is_jump(st):
    if type(st) == ast.Break:
        return BlockType.BREAK
    elif type(st) == ast.Continue:
        return BlockType.CONTINUE
    elif type(st) == ast.Return:
        return BlockType.RETURN
    return -1


def is_st_comment(st):
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
        if st.value.value.startswith("'") or st.value.value.startswith("#"):
            return True
    return False


class JumpNode:
    def __init__(self, block_type, node):
        self.__type: BlockType = block_type
        self.__meta_score = 2
        self.__ast_node = node

    def get_type(self):
        return self.__type

    def get_ast_node(self):
        return self.__ast_node

    def get_meta_score(self):
        return self.__meta_score


class BlockNode:
    def __init__(self, block_type, p_block=None):
        self.__parent = None
        self.__isEmpty = True
        self.__type: BlockType = block_type
        self.__parent: BlockNode = p_block
        self.__metaIndex = -1
        self.__jumpBlock = None
        self.__children = []
        self.__ast_nodes = []
        self.__variables = []
        self.__inValues = None
        self.__outValues = None
        self.__values = None
        self.__meta_score = 1
        self.__CONTROL_META_SCORE = 2
        self.__visit = 0

    def set_meta_index(self, index):
        self.__metaIndex = index

    def get_meta_index(self):
        return self.__metaIndex

    def get_visit(self):
        return self.__visit

    def update_visit(self):
        self.__visit += 1

    def add_inValue(self, value):
        if self.__inValues is not None:
            self.__inValues.append(value)
        else:
            self.__inValues = []
            self.__inValues.append(value)

    def add_outValue(self, value):
        if self.__outValues is not None:
            self.__outValues.append(value)
        else:
            self.__outValues = []
            self.__outValues.append(value)

    def add_value(self, value):
        if self.__values is not None:
            self.__values.append(value)
        else:
            self.__values = []
            self.__values.append(value)

    def get_inValues(self):
        return self.__inValues

    def get_outValues(self):
        return self.__outValues

    def get_ast_nodes(self):
        return self.__ast_nodes

    def set_ast_nodes(self, ast_nodes):
        self.__ast_nodes = ast_nodes

    def get_jump_block(self):
        return self.__jumpBlock

    def get_type(self):
        return self.__type

    def add_ast_node(self, node):
        self.__isEmpty = False
        self.__ast_nodes.append(node)

    def add_children(self, c_block):
        self.__children.append(c_block)

    def set_jump_block(self, jump_block):
        self.__jumpBlock = jump_block

    def set_parent(self, p_block):
        self.__parent = p_block

    def get_children(self):
        return self.__children

    def set_meta_score(self):
        self.__meta_score = self.__CONTROL_META_SCORE

    def get_meta_score(self):
        return self.__meta_score

    def set_inValues(self, inValues):
        self.__inValues = inValues

    def set_outValues(self, outValues):
        self.__outValues = outValues


class BlockBuilder(ast.NodeVisitor):
    def __init__(self, m_node):
        self.__root_block = None
        self.__root_block: BlockNode
        self.__meta_blocks = []
        self.__m_node = m_node
        self.__block_index_map = {}
        self.__test_trace = []
        self.visit(m_node)
        self.init_block_index_map()

    def init_block_index_map(self):
        i = 0
        for block_node in self.__meta_blocks:
            self.__block_index_map[block_node] = i
            block_node.set_meta_index(i)
            i += 1

    def add_test_trace(self, index):
        self.__test_trace.append(index)

    def init_specification_body(self, block_node):
        for i in range(1, len(block_node.get_children())-1):
            cur_block: BlockNode = block_node.get_children()[i]
            if cur_block.get_inValues() is not None:
                continue
            if cur_block.get_type() == BlockType.BASIC_BLOCK:
                continue
            else:
                cur_block.set_inValues(block_node.get_children()[i-1].get_inValues())
                cur_block.set_outValues(block_node.get_children()[i+1].get_inValues())
                if cur_block.get_type() == BlockType.IF_BLOCK:
                    self.init_specification_If(cur_block, block_node.get_children()[i-1], block_node.get_children()[i+1])
                elif cur_block.get_type() == BlockType.FOREACH_BLOCK:
                    self.init_specification_for(cur_block, block_node.get_children()[i-1], block_node.get_children()[i+1])
                elif cur_block.get_type() == BlockType.WHILE_BLOCK:
                    self.init_specification_while(cur_block, block_node.get_children()[i-1], block_node.get_children()[i+1])

    def init_specification_If(self, block_node, pre_block: BlockNode, next_block: BlockNode):
        if block_node.get_inValues() is None:
            return
        if_cond: BlockNode = block_node.get_children()[0]
        if_cond.set_inValues(block_node.get_inValues())
        index = self.__block_index_map.get(pre_block)
        if_body: BlockNode = block_node.get_children()[1]
        if_body.set_inValues(if_body.get_children()[0].get_inValues())
        s = 0
        t = 0
        else_body = None
        if len(block_node.get_children()) == 3:
            else_body = block_node.get_children()[2]
            else_body.set_inValues(else_body.get_children()[0].get_inValues())
        for i in range(len(self.__test_trace)):
            if self.__test_trace[i] == index:
                if i == (len(self.__test_trace) - 1):
                    if_cond.add_value(None)
                else:
                    j = self.__test_trace[i + 1]
                    if j == index + 2:
                        if_cond.add_value(True)
                        if self.__meta_blocks[j].get_inValues() is not None:
                            if_cond.add_outValue(self.__meta_blocks[j].get_inValues()[s])
                        if next_block.get_outValues() is None or len(next_block.get_outValues()) < s+t+1:
                            if_body.add_outValue(None)
                        else:
                            if_body.add_outValue(next_block.get_outValues()[s+t])
                        s += 1
                    else:
                        if_cond.add_value(False)
                        if self.__meta_blocks[j].get_inValues() is not None:
                            if_cond.add_outValue(self.__meta_blocks[j].get_inValues()[t])
                        if else_body is not None:
                            if next_block.get_outValues() is None or len(next_block.get_outValues()) < s + t + 1:
                                else_body.add_outValue(None)
                            else:
                                else_body.add_outValue(next_block.get_outValues()[s + t])
                        t += 1
        self.init_specification_body(if_body)
        if else_body is not None:
            self.init_specification_body(else_body)

    def init_specification_while(self, block_node, pre_block, next_block):
        if block_node.get_inValues() is None:
            return
        pre_index = self.__block_index_map.get(pre_block)
        next_index = self.__block_index_map.get(next_block)
        while_cond: BlockNode = block_node.get_children()[0]
        while_body: BlockNode = block_node.get_children()[1]
        while_body.set_inValues(while_body.get_children()[0].get_inValues())
        s = 0
        t = 0
        r = 0
        li = []
        for i in range(len(self.__test_trace)):
            if self.__test_trace[i] == pre_index:
                li.append(i)
        for i in range(len(li)):
            pre = 0
            nxt = 0
            if i < len(li) -1:
                pre = li[i]
                nxt = li[i+1]
            else:
                pre = li[i]
                nxt = len(self.__test_trace)
            if pre == len(self.__test_trace) -1:
                break
            while_cond.add_inValue(block_node.get_inValues()[i])
            k = self.__test_trace[li[i] + 1]
            if k == pre_index + 2:
                while_cond.add_value(True)
                while_cond.add_outValue(while_body.get_inValues()[s])
                s += 1
                for j in range(pre+2, nxt):
                    k = self.__test_trace[j]
                    if k == pre_index + 2:
                        while_cond.add_value(True)
                        p_block = self.__meta_blocks[self.__test_trace[j-1]]
                        while_body.add_outValue(p_block.get_outValues()[t])
                        while_cond.add_inValue(p_block.get_outValues()[t])
                        while_cond.add_outValue(while_body.get_inValues()[s])
                        t += 1
                        s += 1
                    elif k == next_index:
                        m = self.__test_trace[j-1]
                        p_block = self.__meta_blocks[m]
                        if p_block.get_jump_block() is None:
                            while_cond.add_value(False)
                            while_body.add_outValue(p_block.get_outValues()[t])
                            while_cond.add_inValue(p_block.get_outValues()[t])
                            while_cond.add_outValue(next_block.get_inValues()[r])
                            t += 1
                            r += 1
                        else:
                            while_body.add_outValue(p_block.get_outValues()[t])
                            t += 1
                            r += 1
            else:
                while_cond.add_value(False)
                while_cond.add_outValue(next_block.get_inValues()[r])
                r += 1
        self.init_specification_body(while_body)

    def init_specification_for(self, block_node: BlockNode, pre_block, next_block):
        if block_node.get_inValues() is None:
            return
        pre_index = self.__block_index_map.get(pre_block)
        nxt_index = self.__block_index_map.get(next_block)
        for_iter = block_node.get_children()[0]
        for_body = block_node.get_children()[1]
        for_body.set_inValues(for_body.get_children()[0].get_inValues())
        s = 0
        t = 0
        r = 0
        li = []
        for i in range(len(self.__test_trace)):
            if self.__test_trace[i] == pre_index:
                li.append(i)
        for i in range(len(li)):
            pre = 0
            nxt = 0
            if i < len(li) - 1:
                pre = li[i]
                nxt = li[i + 1]
            else:
                pre = li[i]
                nxt = len(self.__test_trace)
            if pre == len(self.__test_trace) -1:
                break
            for_iter.add_inValue(block_node.get_inValues()[i])
            k = self.__test_trace[li[i] + 1]
            if k == pre_index + 2:
                for_iter.add_outValue(for_body.get_inValues()[s])
                s += 1
                for j in range(pre + 2, nxt):
                    k = self.__test_trace[j]
                    if k == pre_index + 2:
                        p_block = self.__meta_blocks[self.__test_trace[j - 1]]
                        for_body.add_outValue(p_block.get_outValues()[t])
                        for_iter.add_inValue(p_block.get_outValues()[t])
                        for_iter.add_outValue(for_body.get_inValues()[s])
                        t += 1
                        s += 1
                    elif k == nxt_index:
                        m = self.__test_trace[j - 1]
                        p_block = self.__meta_blocks[m]
                        if p_block.get_jump_block() is None:
                            for_body.add_outValue(p_block.get_outValues()[t])
                            for_iter.add_inValue(p_block.get_outValues()[t])
                            for_iter.add_outValue(next_block.get_inValues()[r])
                            t += 1
                            r += 1
                        else:
                            for_body.add_outValue(p_block.get_outValues()[t])
                            t += 1
                            r += 1
            else:
                for_iter.add_outValue(next_block.get_inValues()[r])
                r += 1
        self.init_specification_body(for_body)

    def update_m_node(self):
        self.__m_node.body = self.update_node_body(self.__root_block)

    def update_node_body(self, block_node):
        new_body = []
        for block_child in block_node.get_children():
            new_body.extend(block_child.get_ast_nodes())
            if block_child.get_type() == BlockType.BASIC_BLOCK:
                pass
                # if block_child.get_jump_block() is not None:
                #     new_body.append(block_child.get_jump_block().get_ast_node())
            elif block_child.get_type() == BlockType.IF_BLOCK:
                self.update_if_node(block_child)
            elif block_child.get_type() == BlockType.WHILE_BLOCK:
                self.update_while(block_child)
            elif block_child.get_type() == BlockType.FOREACH_BLOCK:
                self.update_For(block_child)
        return new_body

    def update_if_node(self, block_node):
        if_ast_node: If = block_node.get_ast_nodes()[0]
        if_cond = block_node.get_children()[0]
        if_ast_node.test = if_cond.get_ast_nodes()[0]
        if_ast_node.body = self.update_node_body(block_node.get_children()[1])
        if len(block_node.get_children()) == 3:
            if_ast_node.orelse = self.update_node_body(block_node.get_children()[2])

    def update_while(self, block_node):
        while_ast_node: While = block_node.get_ast_nodes()[0]
        while_cond = block_node.get_children()[0]
        while_ast_node.test = while_cond.get_ast_nodes()[0]
        while_ast_node.body = self.update_node_body(block_node.get_children()[1])

    def update_For(self, block_node):
        for_ast_node: For = block_node.get_ast_nodes()[0]
        for_iter = block_node.get_children()[0]
        for_ast_node.target = for_iter.get_ast_nodes()[0]
        for_ast_node.iter = for_iter.get_ast_nodes()[1]
        for_ast_node.body = self.update_node_body(block_node.get_children()[1])

    def get_meta_blocks(self):
        return self.__meta_blocks

    def get_m_node(self):
        return self.__m_node

    def get_root_block(self):
        return self.__root_block

    def visit_body(self, body, p_block):
        pre_block = None
        for st in body:
            block_type = get_block_type(st)
            if pre_block is None or pre_block.get_type() != BlockType.BASIC_BLOCK:
                new_block = BlockNode(BlockType.BASIC_BLOCK, p_block)
                pre_block = new_block
                p_block.add_children(new_block)
                if is_jump(st) != -1:
                    if new_block.get_jump_block() is None:
                        new_block.add_ast_node(st)
                        new_block.set_jump_block(JumpNode(is_jump(st), st))
                elif block_type == -1:
                    if not is_st_comment(st):
                        new_block.add_ast_node(st)
                self.__meta_blocks.append(new_block)
            else:
                if is_jump(st) != -1:
                    if pre_block.get_jump_block() is None:
                        pre_block.add_ast_node(st)
                        pre_block.set_jump_block(JumpNode(is_jump(st), st))
                elif block_type == -1:
                    if not is_st_comment(st):
                        pre_block.add_ast_node(st)
            if block_type != -1:
                new_block = self.visit(st)
                new_block.set_parent(p_block)
                pre_block = new_block
                p_block.add_children(new_block)
        if pre_block is None or pre_block.get_type() != BlockType.BASIC_BLOCK:
            new_block = BlockNode(BlockType.BASIC_BLOCK, p_block)
            p_block.add_children(new_block)
            self.__meta_blocks.append(new_block)

    def visit_FunctionDef(self, node):
        self.__root_block = BlockNode(BlockType.METHOD_ENTRY, None)
        self.__root_block.add_ast_node(node)
        self.visit_body(node.body, self.__root_block)

    def visit_For(self, node: For) -> Any:
        new_block = BlockNode(BlockType.FOREACH_BLOCK)
        new_block.add_ast_node(node)
        new_iter = BlockNode(BlockType.FOREACH_ITER, new_block)
        new_iter.add_ast_node(node.target)
        new_iter.add_ast_node(node.iter)
        new_iter.set_meta_score()
        self.__meta_blocks.append(new_iter)
        new_body = BlockNode(BlockType.FOREACH_BODY, new_block)
        self.visit_body(node.body, new_body)
        new_block.add_children(new_iter)
        new_block.add_children(new_body)
        return new_block

    def visit_While(self, node: While) -> Any:
        new_block = BlockNode(BlockType.WHILE_BLOCK)
        new_block.add_ast_node(node)
        new_cond = BlockNode(BlockType.WHILE_COND, new_block)
        new_cond.add_ast_node(node.test)
        new_cond.set_meta_score()
        self.__meta_blocks.append(new_cond)
        new_body = BlockNode(BlockType.WHILE_BODY, new_block)
        new_body.add_ast_node(node.body)
        self.visit_body(node.body, new_body)
        new_block.add_children(new_cond)
        new_block.add_children(new_body)
        return new_block

    def visit_If(self, node: If) -> Any:
        new_block = BlockNode(BlockType.IF_BLOCK)
        new_block.add_ast_node(node)
        new_cond = BlockNode(BlockType.IF_COND, new_block)
        new_cond.add_ast_node(node.test)
        new_cond.set_meta_score()
        self.__meta_blocks.append(new_cond)
        new_body = BlockNode(BlockType.IF_BODY, new_block)
        new_body.add_ast_node(node.body)
        self.visit_body(node.body, new_body)
        new_block.add_children(new_cond)
        new_block.add_children(new_body)
        if len(node.orelse) != 0:
            new_else_body = BlockNode(BlockType.ELSE_BODY, new_block)
            new_else_body.add_ast_node(node.orelse)
            self.visit_body(node.orelse, new_else_body)
            new_block.add_children(new_else_body)
        return new_block

    def init_specification(self):
        self.init_specification_body(self.__root_block)

from basic_framework.bidirectional_refactoring.cs_node import CSNode, CSType


def is_mapped(node1: CSNode, node2: CSNode):
    if node1.cs_type == node2.cs_type:
        return True
    if node1.cs_type == CSType.ELSE_BRANCH and node2.cs_type == CSType.THEN_BRANCH:
        return True
    if node1.cs_type == CSType.THEN_BRANCH and node2.cs_type == CSType.ELSE_BRANCH:
        return True
    return False


def is_ancestor_map(node1: CSNode, node2: CSNode):
    if node1.ancestorFW is None and node2.ancestorFW is not None:
        return False
    if node2.ancestorFW is None and node1.ancestorFW is not None:
        return False
    if node1.ancestorFW is None and node2.ancestorFW is None:
        return True
    if len(node1.ancestorFW) != len(node2.ancestorFW):
        return False
    for i in range(len(node1.ancestorFW)):
        if node1.ancestorFW[i].cs_type != node2.ancestorFW[i].cs_type:
            return False
    return True


class RoughMapping:
    def __init__(self, src: CSNode, dst: CSNode):
        self.src = src
        self.dst = dst
        self.src_nodes = []
        self.dst_nodes = []
        self.M = 0
        self.N = 0
        self.mapping_scores = []
        self.mapping_score = 0

    def mapping(self):
        self.src_dfs_init(self.src)
        self.dst_dfs_init(self.dst)
        self.mapping_init()
        self.rough_mapping()

    def src_dfs_init(self, node: CSNode):
        self.src_nodes.append(node)
        # print(node.cs_type, node.height)
        for child in node.children:
            self.src_dfs_init(child)

    def dst_dfs_init(self, node: CSNode):
        self.dst_nodes.append(node)
        # print(node.cs_type, node.height)
        for child in node.children:
            self.dst_dfs_init(child)

    def mapping_init(self):
        self.M = len(self.src_nodes)
        self.N = len(self.dst_nodes)
        for i in range(self.M + 1):
            temp = [0]
            for j in range(self.N):
                temp.append(0)
            self.mapping_scores.append(temp)

    def rough_mapping(self):
        for i in range(1, self.M + 1):
            for j in range(1, self.N + 1):
                flag = is_mapped(self.src_nodes[i - 1], self.dst_nodes[j - 1]) and is_ancestor_map(
                    self.src_nodes[i - 1], self.dst_nodes[j - 1])
                self.mapping_scores[i][j] = max(self.mapping_scores[i - 1][j - 1]+flag, self.mapping_scores[i - 1][j],
                                                self.mapping_scores[i][j - 1])
        self.mapping_score = self.mapping_scores[self.M][self.N]


class LoopMapping(RoughMapping):
    def __init__(self, src: CSNode, dst: CSNode):
        super().__init__(src, dst)

    def mapping(self):
        self.src_dfs_init(self.src)
        self.dst_dfs_init(self.dst)
        self.mapping_init()
        self.rough_mapping()

    def src_dfs_init(self, node: CSNode):
        if node.cs_type == CSType.METHOD_DECLARATION or node.cs_type == CSType.FOR_STMT or node.cs_type == CSType.WHILE_STMT:
            self.src_nodes.append(node)
            # print(node.cs_type, node.height)
        for child in node.children:
            self.src_dfs_init(child)

    def dst_dfs_init(self, node: CSNode):
        if node.cs_type == CSType.METHOD_DECLARATION or node.cs_type == CSType.FOR_STMT or node.cs_type == CSType.WHILE_STMT:
            self.dst_nodes.append(node)
            # print(node.cs_type, node.height)
        for child in node.children:
            self.dst_dfs_init(child)


class Mapping:
    def __init__(self, src: CSNode, dst: CSNode):
        self.src = src
        self.dst = dst
        self.src_to_dst = {}
        self.dst_to_src = {}
        self.src_nodes = []
        self.dst_nodes = []
        self.M = 0
        self.N = 0
        self.mapping_scores = []
        self.mapping_pairs = []
        self.src_tree_index = {}
        self.dst_tree_index = {}
        self.mappings = None
        self.mapping_score = 0
        self.mapping_fw_score = 0

        self.src_dfs_init(src)
        self.dst_dfs_init(dst)
        self.mapping_init()
        self.mapping_algorithm()
        self.fill_mapping()

    def src_dfs_init(self, node: CSNode):
        self.src_nodes.append(node)
        self.src_tree_index[node] = len(self.src_tree_index)
        # print(node.cs_type, node.height)
        for child in node.children:
            self.src_dfs_init(child)

    def dst_dfs_init(self, node: CSNode):
        self.dst_nodes.append(node)
        self.dst_tree_index[node] = len(self.dst_tree_index)
        # print(node.cs_type, node.height)
        for child in node.children:
            self.dst_dfs_init(child)

    def mapping_init(self):
        self.M = len(self.src_nodes)
        self.N = len(self.dst_nodes)

        for i in range(self.M + 1):
            temp = [0]
            # temp2 = [""]
            temp2 = [{""}]
            for j in range(self.N):
                temp.append(0)
                # temp2.append("")
                temp2.append({""})
            self.mapping_scores.append(temp)
            self.mapping_pairs.append(temp2)

    # def height_diff(self, node1: CSNode, node2: CSNode):
    #     return abs(node1.height - node2.height) < 3

    def is_legal_insertion(self, n1, n2, maps: str):
        if n1.cs_type == CSType.ELSE_BRANCH or n1.cs_type == CSType.THEN_BRANCH:
            n1p_i = self.src_nodes.index(n1.parent)
            n2p_i = self.dst_nodes.index(n2.parent)
            if maps.find(str.format(";{0},{1};", n1p_i, n2p_i)) != -1:
                return True
            else:
                return False
        if n1.ancestor is not None:
            for anc1 in n1.ancestor:
                n1p_i = self.src_nodes.index(anc1)
                if n1p_i == 0:
                    break
                t_i = maps.find(str.format(";{0},", n1p_i))
                if t_i != -1:
                    t_i = t_i + len(str.format(";{0},", n1p_i))
                    t_i = int(maps[t_i:].split(";")[0])
                    if self.dst_nodes[t_i] not in n2.ancestor:
                        return False

        if n2.ancestor is not None:
            for anc2 in n2.ancestor:
                n2p_i = self.dst_nodes.index(anc2)
                if n2p_i == 0:
                    return True
                t_i = maps.find(str.format(",{0};", n2p_i))
                if t_i != -1:
                    t_i = int(maps[0:t_i].split(";")[-1])
                    if self.src_nodes[t_i] not in n1.ancestor:
                        return False
        return True

    def is_legal_matching(self, n1, n2, maps: str):
        if n1.ancestor is not None:
            for anc1 in n1.ancestor:
                if anc1.cs_type == CSType.ELSE_BRANCH:
                    n1p_i = self.src_nodes.index(anc1)
                    t_i = maps.find(str.format(";{0},", n1p_i))
                    if t_i == -1:
                        _then = anc1.parent.children[0]
                        then_i = self.src_nodes.index(_then)
                        for i in range(then_i, n1p_i):
                            if maps.find(str.format(";{0},", i)) != -1:
                                return False
        if n2.ancestor is not None:
            for anc2 in n2.ancestor:
                if anc2.cs_type == CSType.ELSE_BRANCH:
                    n2p_i = self.dst_nodes.index(anc2)
                    t_i = maps.find(str.format(",{0};", n2p_i))
                    if t_i == -1:
                        _then = anc2.parent.children[0]
                        then_i = self.dst_nodes.index(_then)
                        for i in range(then_i, n2p_i):
                            if maps.find(str.format(",{0};", i)) != -1:
                                return False
        return True

    def mapping_algorithm(self):
        for i in range(1, self.M + 1):
            for j in range(1, self.N + 1):
                self.mapping_pairs[i][j].remove("")
                flag = is_mapped(self.src_nodes[i - 1], self.dst_nodes[j - 1]) and is_ancestor_map(
                    self.src_nodes[i - 1], self.dst_nodes[j - 1])
                a = self.mapping_scores[i - 1][j - 1]
                b = self.mapping_scores[i - 1][j]
                c = self.mapping_scores[i][j - 1]
                inc = 0
                self.mapping_pairs[i][j].update(self.mapping_pairs[i - 1][j] - self.mapping_pairs[i - 1][j - 1])
                self.mapping_pairs[i][j].update(self.mapping_pairs[i][j - 1] - self.mapping_pairs[i - 1][j - 1])
                if flag == 1:
                    pair = str.format('{0},{1};', i - 1, j - 1)
                    flag_in = False
                    for mappings in self.mapping_pairs[i - 1][j - 1]:
                        if self.is_legal_insertion(self.src_nodes[i - 1], self.dst_nodes[j - 1], mappings) \
                                and self.is_legal_matching(self.src_nodes[i - 1], self.dst_nodes[j - 1], mappings):
                            self.mapping_pairs[i][j].add(mappings + pair)
                            flag_in = True
                            if (mappings + pair).count(";") > a:
                                inc = 1
                        elif mappings in self.mapping_pairs[i - 1][j] and mappings in self.mapping_pairs[i][j-1]:
                            self.mapping_pairs[i][j].add(mappings)
                    if not flag_in:
                        temp_i = i - 1
                        temp_j = j - 1
                        while not flag_in and temp_i >= 1 and temp_j >= 1:
                            for mappings in self.mapping_pairs[temp_i - 1][temp_j - 1]:
                                if self.is_legal_insertion(self.src_nodes[i - 1], self.dst_nodes[j - 1],
                                                           mappings):
                                    self.mapping_pairs[i][j].add(mappings + pair)
                                    flag_in = True
                            temp_i -= 1
                            temp_j -= 1
                else:
                    for mappings in self.mapping_pairs[i - 1][j - 1]:
                        if mappings in self.mapping_pairs[i - 1][j] and mappings in self.mapping_pairs[i][j - 1]:
                            self.mapping_pairs[i][j].add(mappings)
                ma = max(a + inc, b, c)
                self.mapping_scores[i][j] = ma
            # print(self.mapping_scores)
        # print(self.mapping_scores[self.M][self.N])
        # print(len(self.mapping_pairs[self.M][self.N]))
        # print(self.mapping_pairs[self.M][self.N])
        self.find_best_match()
        # print(self.mappings)

    def mapping_algorithm_n(self):
        for i in range(1, self.M + 1):
            for j in range(1, self.N + 1):
                self.mapping_pairs[i][j].remove("")
                flag = is_mapped(self.src_nodes[i - 1], self.dst_nodes[j - 1]) and is_ancestor_map(
                    self.src_nodes[i - 1], self.dst_nodes[j - 1])
                a = self.mapping_scores[i - 1][j - 1]
                b = self.mapping_scores[i - 1][j]
                c = self.mapping_scores[i][j - 1]
                min_a = False
                inc = 0
                if b > c:
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i - 1][j])
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i][j-1] - self.mapping_pairs[i-1][j-1])
                elif c > b:
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i][j - 1])
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i-1][j] - self.mapping_pairs[i - 1][j - 1])
                elif c == b and c > a:
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i][j - 1])
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i - 1][j])
                elif flag == 0:  # a==b, a==c, flag = 0
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i][j - 1])
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i - 1][j])
                else:
                    min_a = True
                if flag == 1:
                    pair = str.format('{0},{1};', i - 1, j - 1)
                    flag_in = False
                    for mappings in self.mapping_pairs[i - 1][j - 1]:
                        if self.is_legal_insertion(self.src_nodes[i - 1], self.dst_nodes[j - 1], mappings) \
                                and self.is_legal_matching(self.src_nodes[i - 1], self.dst_nodes[j - 1], mappings):
                            self.mapping_pairs[i][j].add(mappings + pair)
                            flag_in = True
                            if (mappings + pair).count(";") > a:
                                inc = 1
                        elif min_a:
                            self.mapping_pairs[i][j].add(mappings)
                    if not flag_in:
                        temp_i = i - 1
                        temp_j = j - 1
                        while not flag_in and temp_i >= 1 and temp_j >= 1:
                            for mappings in self.mapping_pairs[temp_i - 1][temp_j - 1]:
                                if self.is_legal_insertion(self.src_nodes[i - 1], self.dst_nodes[j - 1],
                                                           mappings):
                                    self.mapping_pairs[i][j].add(mappings + pair)
                                    flag_in = True
                            temp_i -= 1
                            temp_j -= 1
                if inc == 0 and min_a:
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i][j - 1])
                    self.mapping_pairs[i][j].update(self.mapping_pairs[i - 1][j])
                ma = max(a + inc, b, c)
                self.mapping_scores[i][j] = ma
            # print(self.mapping_scores)
        # print(self.mapping_scores[self.M][self.N])
        # print(len(self.mapping_pairs[self.M][self.N]))
        # print(self.mapping_pairs[self.M][self.N])
        self.find_best_match()
        # print(self.mappings)

    def mapping(self):
        for i in range(1, self.M + 1):
            for j in range(1, self.N + 1):
                flag = is_mapped(self.src_nodes[i - 1], self.dst_nodes[j - 1]) \
                       and is_ancestor_map(self.src_nodes[i - 1], self.dst_nodes[j - 1])
                a = self.mapping_scores[i - 1][j - 1]
                b = self.mapping_scores[i - 1][j]
                c = self.mapping_scores[i][j - 1]
                min_a = False
                inc = 0
                new_mappings = []
                if flag == 1:
                    pair = str.format('{0},{1};', i - 1, j - 1)
                    flag_in = False
                    for k in range(len(self.mapping_pairs[i - 1][j - 1])):
                        if self.is_legal_insertion(self.src_nodes[i - 1], self.dst_nodes[j - 1],
                                                   self.mapping_pairs[i - 1][j - 1][k]):
                            new_mappings.append(self.mapping_pairs[i - 1][j - 1][k] + pair)
                            flag_in = True
                            if new_mappings[-1].count(";") > a:
                                inc = 1
                        else:
                            new_mappings.append(self.mapping_pairs[i - 1][j - 1])
                    if not flag_in:
                        temp_i = i - 1
                        temp_j = j - 1
                        while not flag_in and temp_i >= 1 and temp_j >= 1:
                            for k in range(len(self.mapping_pairs[temp_i - 1][temp_j - 1])):
                                if self.is_legal_insertion(self.src_nodes[i - 1], self.dst_nodes[j - 1],
                                                           self.mapping_pairs[temp_i - 1][temp_j - 1][k]):
                                    self.mapping_pairs[i][j].append(
                                        self.mapping_pairs[temp_i - 1][temp_j - 1][k] + pair)
                                    flag_in = True
                            temp_i -= 1
                            temp_j -= 1

                else:
                    new_mappings.extend(self.mapping_pairs[i - 1][j - 1])
                for k in range(len(self.mapping_pairs[i - 1][j - 1])):
                    pa = self.mapping_pairs[i - 1][j - 1].count(";")
                    pb = self.mapping_pairs[i - 1][j][k].count(";")
                    pc = self.mapping_pairs[i][j - 1][k].count(";")
                    pd = new_mappings[k].count(";")
                    if pc > pb:
                        self.mapping_pairs[i][j].append(self.mapping_pairs[i][j - 1][k])
                    elif pb > pc:
                        self.mapping_pairs[i][j].append(self.mapping_pairs[i - 1][j][k])
                    elif pc == pb and pc > pa:
                        self.mapping_pairs[i][j].append(self.mapping_pairs[i][j - 1][k])
                        new_mappings.append(self.mapping_pairs[i - 1][j][k])
                    elif pd > pa:
                        self.mapping_pairs[i][j].append(new_mappings[k])
                        new_mappings.pop(k)
                    else:
                        self.mapping_pairs[i][j].append(new_mappings[k])
                        new_mappings.pop(k)

                    if pa == pb and new_mappings[k] != self.mapping_pairs[i - 1][j][k]:
                        new_mappings.append(self.mapping_pairs[i - 1][j][k])
                    if pc == pa and new_mappings[k] != self.mapping_pairs[i][j - 1][k]:
                        new_mappings.append(self.mapping_pairs[i][j - 1][k])
                    if pb > pa:
                        new_mappings[k] = self.mapping_pairs[i - 1][j][k]
                        if pc > pa:
                            new_mappings.append(self.mapping_pairs[i][j - 1][k])
                    elif pc > pa:
                        new_mappings[k] = self.mapping_pairs[i][j - 1][k]

                ma = max(a + inc, b, c)
                self.mapping_scores[i][j] = ma
                self.mapping_pairs[i][j] = new_mappings
        print(self.M)
        print(self.N)
        # print(self.mapping_scores)
        print(self.mapping_scores[self.M][self.N])
        print(len(self.mapping_pairs[self.M][self.N]))
        print(self.mapping_pairs[self.M][self.N])
        self.find_best_match()
        print(self.mappings)

    def mapping_algorithm1(self):
        for i in range(1, self.M + 1):
            for j in range(1, self.N + 1):
                flag = is_mapped(self.src_nodes[i - 1], self.dst_nodes[j - 1]) \
                       and is_ancestor_map(self.src_nodes[i - 1], self.dst_nodes[j - 1])
                if flag:
                    is_map = 1
                else:
                    is_map = 0
                a = self.mapping_scores[i - 1][j - 1] + is_map
                b = self.mapping_scores[i - 1][j]
                c = self.mapping_scores[i][j - 1]
                if (self.src_nodes[i - 1].cs_type is not CSType.FOR_STMT
                    and self.src_nodes[i - 1].cs_type is not CSType.WHILE_STMT) \
                        and (is_map == 1 and (a == b and a > c)):
                    inn = (str(self.mapping_pairs[i - 1][j])).rfind(";")
                    if inn == -1:
                        pair = self.mapping_pairs[i - 1][j]
                    else:
                        pair = (str(self.mapping_pairs[i - 1][j]))[inn + 1:]
                    index = int(pair.split(",")[0])
                    # print(pair)
                    # print(index)
                    d: CSNode = self.dst_nodes[j - 1]
                    s: CSNode = self.src_nodes[i - 1]
                    ss: CSNode = self.src_nodes[index - 1]
                    dp: CSNode = d.parent
                    sp: CSNode = s.parent
                    ssp: CSNode = ss.parent

                    dpi = self.dst_tree_index.get(dp) + 1
                    spi = self.src_tree_index.get(sp) + 1
                    sspi = self.src_tree_index.get(ssp) + 1
                    p1 = str.format("{0},{1}", spi, dpi)
                    p2 = str.format("{0},{1}", sspi, dpi)
                    if spi == sspi:
                        self.set_mapA(i, j, a, is_map)
                    elif (str(self.mapping_pairs[i - 1][j])).find(p2) != -1:
                        self.set_mapB(i, j, b)
                    elif (str(self.mapping_pairs[i - 1][j])).find(p1) != -1:
                        self.set_mapA(i, j, a, is_map)
                    else:
                        self.set_mapB(i, j, b)
                elif (self.src_nodes[i - 1].cs_type is not CSType.FOR_STMT
                      and self.src_nodes[i - 1].cs_type is not CSType.WHILE_STMT) \
                        and is_map == 1 and (a == c and a > b):
                    inn = (str(self.mapping_pairs[i][j - 1])).rfind(";")
                    if inn == -1:
                        pair = self.mapping_pairs[i][j - 1]
                    else:
                        pair = (str(self.mapping_pairs[i][j - 1]))[inn:]

                    index = int(pair.split(",")[1])
                    d: CSNode = self.dst_nodes[j - 1]
                    s: CSNode = self.src_nodes[i - 1]
                    dd: CSNode = self.dst_nodes[index - 1]
                    dp: CSNode = d.parent
                    sp: CSNode = s.parent
                    ddp: CSNode = dd.parent
                    dpi = self.dst_tree_index.get(dp) + 1
                    spi = self.src_tree_index.get(sp) + 1
                    ddpi = self.dst_tree_index.get(ddp) + 1
                    p1 = str.format("{0},{1}", spi, dpi)
                    p2 = str.format("{0},{1}", spi, ddpi)
                    if dpi == ddpi:
                        self.set_mapA(i, j, a, is_map)
                    elif (str(self.mapping_pairs[i][j - 1])).find(p2) != -1:
                        self.set_mapC(i, j, c)
                    elif (str(self.mapping_pairs[i][j - 1])).find(p1) != -1:
                        self.set_mapA(i, j, a, is_map)
                    else:
                        self.set_mapC(i, j, c)
                elif (self.src_nodes[i - 1].cs_type is not CSType.FOR_STMT
                      and self.src_nodes[i - 1].cs_type is not CSType.WHILE_STMT) \
                        and is_map == 1 and (a == b and a == c):
                    self.set_mapA(i, j, a, is_map)
                else:
                    if b >= a:
                        if b >= c:
                            self.set_mapB(i, j, b)
                        else:
                            self.set_mapC(i, j, c)
                    else:
                        if c >= a:
                            self.set_mapC(i, j, c)
                        else:
                            self.set_mapA(i, j, a, is_map)
        self.mappings = self.mapping_pairs[self.M][self.N]

    def mapping_algorithm2(self):
        for i in range(1, self.M + 1):
            for j in range(1, self.N + 1):
                self.mapping_pairs[i][j].remove("")
                flag = is_mapped(self.src_nodes[i - 1], self.dst_nodes[j - 1]) and is_ancestor_map(
                    self.src_nodes[i - 1], self.dst_nodes[j - 1])
                flag_a = False
                temp = []
                inc = 0
                a = self.mapping_scores[i - 1][j - 1]
                b = self.mapping_scores[i - 1][j]
                c = self.mapping_scores[i][j - 1]
                if flag == 1:
                    pair = str.format('{0},{1};', i - 1, j - 1)
                    for k in range(len(self.mapping_pairs[i - 1][j - 1])):
                        if self.is_legal_insertion(self.src_nodes[i - 1], self.dst_nodes[j - 1],
                                                   self.mapping_pairs[i - 1][j - 1][k]):
                            temp.append(self.mapping_pairs[i - 1][j - 1][k] + pair)
                            if temp[-1].count(";") > a:
                                inc = 1
                        else:
                            self.mapping_pairs[i][j].append(self.mapping_pairs[i - 1][j - 1][k])

                ma = max(a + inc, b, c)
                self.mapping_scores[i][j] = ma

                if not flag and ma == a:
                    flag_a = True
                    for pairs in self.mapping_pairs[i - 1][j - 1]:
                        self.mapping_pairs[i][j].append(pairs)
                if flag and not inc:
                    flag_a = True
                if ma == b:
                    if not flag_a:
                        for pairs in self.mapping_pairs[i - 1][j]:
                            self.mapping_pairs[i][j].append(pairs)
                    else:
                        for k in range(len(self.mapping_pairs[i - 1][j - 1]), len(self.mapping_pairs[i - 1][j])):
                            self.mapping_pairs[i][j].append(self.mapping_pairs[i - 1][j][k])
                if ma == c:
                    if not flag_a:
                        for pairs in self.mapping_pairs[i][j - 1]:
                            self.mapping_pairs[i][j].append(pairs)
                    else:
                        for k in range(len(self.mapping_pairs[i - 1][j - 1]), len(self.mapping_pairs[i][j - 1])):
                            self.mapping_pairs[i][j].append(self.mapping_pairs[i][j - 1][k])
                if flag == 1:
                    self.mapping_pairs[i][j].extend(temp)
        self.find_best_match()

    def set_ancestor_match(self, cs_node: CSNode):
        if cs_node.get_parent() is not None and not cs_node.get_parent().get_has_d_be_matched():
            cs_node.get_parent().set_has_d_be_matched()
            self.set_ancestor_match(cs_node.get_parent())

    def fill_mapping(self):
        pairs = (str(self.mappings[:-1])).split(";")
        for pair in pairs:
            self.src_to_dst[self.src_nodes[int(pair.split(",")[0])]] = self.dst_nodes[int(pair.split(",")[1])]
            self.dst_to_src[self.dst_nodes[int(pair.split(",")[1])]] = self.src_nodes[int(pair.split(",")[0])]
            self.set_ancestor_match(self.src_nodes[int(pair.split(",")[0])])
            self.set_ancestor_match(self.dst_nodes[int(pair.split(",")[1])])

    def set_mapA(self, i, j, a, is_map):
        self.mapping_scores[i][j] = a
        if is_map == 0:
            self.mapping_pairs[i][j] = self.mapping_pairs[i][j]
        else:
            if len(self.mapping_pairs[i - 1][j - 1]) == 0:
                self.mapping_pairs[i][j] = "".join(
                    ((str(self.mapping_pairs[i - 1][j - 1])), str.format("{0},{1}", i, j)))
            else:
                self.mapping_pairs[i][j] = "".join(
                    ((str(self.mapping_pairs[i - 1][j - 1])), str.format(";{0},{1}", i, j)))
                print(self.mapping_pairs[i][j])

    def set_mapB(self, i, j, b):
        self.mapping_scores[i][j] = b
        self.mapping_pairs[i][j] = self.mapping_pairs[i - 1][j]

    def set_mapC(self, i, j, c):
        self.mapping_scores[i][j] = c
        self.mapping_pairs[i][j] = self.mapping_pairs[i][j - 1]

    def to_string(self):
        for key in self.src_to_dst.keys():
            print(key.cs_type)
            print(self.src_to_dst.get(key).cs_type)

    def find_best_match(self):
        max_fw = 0
        max_pair = 0

        for pairs in sorted(self.mapping_pairs[self.M][self.N],key=lambda x:(len(x),x)):
            count = 0
            count_fw = 0
            for pair in pairs[:-1].split(";"):
                count += 1
                i = int(pair.split(",")[0])
                if self.src_nodes[i].cs_type == CSType.FOR_STMT or self.src_nodes[i].cs_type == CSType.WHILE_STMT:
                    count_fw += 1
            if count_fw > max_fw:
                max_fw = count_fw
                max_pair = count
                self.mappings = pairs
            elif count_fw == max_fw and count > max_pair:
                self.mappings = pairs
                max_pair = count
                self.mappings = pairs
        self.mapping_score = max_pair
        self.mapping_fw_score = max_fw

    def is_branch_cross_match(self):
        for src, dst in self.src_to_dst.items():
            if src.cs_type == CSType.THEN_BRANCH and dst.cs_type == CSType.ELSE_BRANCH:
                return True
            elif src.cs_type == CSType.ELSE_BRANCH and dst.cs_type == CSType.THEN_BRANCH:
                return True
        return False

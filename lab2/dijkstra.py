class Dijkstra:

    def __init__(self, hosts, switches):
        self.nodes = switches + hosts
        self.path_length = {}
        for i in range(len(self.nodes)):
            self.__dijkstra(i)

    # list of edge
    def get_path(self, n1, n2):
        pass

    def get_path_length(self, n1, n2):
        return self.path_length[(n1.id, n2.id)]

    def __dijkstra(self, index):
        nodes_info = [[node, False, float('inf')] for node in self.nodes]
        nodes_info[index][2] = 0
        while 1:
            next_index = -1
            for i in range(len(nodes_info)):
                if nodes_info[i][1] == False and (next_index == -1 or nodes_info[i][2] < nodes_info[next_index][2]):
                    next_index = i
            if next_index == -1:
                break
            nodes_info[next_index][1] = True
            connect_node = {edge.lnode for edge in nodes_info[next_index][0].edges}.union({edge.rnode for edge in nodes_info[next_index][0].edges})
            connect_node.remove(nodes_info[next_index][0])
            for i in range(len(nodes_info)):
                if nodes_info[i][0] in connect_node and nodes_info[i][1] == False:
                    if nodes_info[i][2] > nodes_info[next_index][2] + 1:
                        nodes_info[i][2] = nodes_info[next_index][2] + 1
        for node_info in nodes_info:
            self.path_length[(self.nodes[index].id, node_info[0].id)] = node_info[2]

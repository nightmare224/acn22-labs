from topo import Edge
from heapq import heappush, heappop

class info:
    def __init__(self, node):
        self.node = node
        self.visited = False
        self.path_length = float('inf')
        self.path = []
    
    def __lt__(self, other_info):
        return self.path_length < other_info.path_length

class Dijkstra:

    def __init__(self, hosts, switches):
        self.num_switches = len(switches)
        self.nodes = switches + hosts
        self.path = {}
        for i in range(len(self.nodes)):
            self.__dijkstra(i)

    # list of edge
    def get_path(self, n1, n2):
        return self.path[(n1, n2)]

    def get_path_length(self, n1, n2):
        return len(self.path[(n1, n2)])

    def __dijkstra(self, index):
        nodes_info = [info(node) for node in self.nodes]
        nodes_info[index].path_length = 0
        heap = []
        heappush(heap, nodes_info[index])
        while heap:
            curr_node_info = heappop(heap)
            curr_node_info.visited = True
            connect_nodes = {edge.lnode if edge.rnode is curr_node_info.node else edge.rnode for edge in curr_node_info.node.edges}
            connect_nodes_info = {node_info for node_info in nodes_info if node_info.node in connect_nodes}
            for connect_node_info in connect_nodes_info:
                if connect_node_info.visited == False:
                    if connect_node_info.path_length > curr_node_info.path_length + 1:
                        connect_node_info.path_length = curr_node_info.path_length + 1
                        connect_node_info.path.clear()
                        if curr_node_info.path:
                            for path in curr_node_info.path:
                                connect_node_info.path.append(path + (Edge(curr_node_info.node, connect_node_info.node),))
                        else:
                            connect_node_info.path.append((Edge(curr_node_info.node, connect_node_info.node),))
                        heappush(heap, connect_node_info)
                    elif connect_node_info.path_length == curr_node_info.path_length + 1:
                        if curr_node_info.path:
                            for path in curr_node_info.path:
                                connect_node_info.path.append(path + (Edge(curr_node_info.node, connect_node_info.node),))
                        else:
                            connect_node_info.path.append((Edge(curr_node_info.node, connect_node_info.node),))
        for i in range(self.num_switches, len(self.nodes)):
            self.path[(self.nodes[index], nodes_info[i].node)] = nodes_info[i].path

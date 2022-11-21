from heapq import heappush, heappop

class info:
    def __init__(self, node):
        self.node = node
        self.visited = False
        self.path_length = float('inf')
        self.parent = []
    
    def __lt__(self, other_info):
        return self.path_length < other_info.path_length

class Dijkstra:

    def __init__(self, hosts, switches):
        self.num_switches = len(switches)
        self.nodes = switches + hosts
        self.path_length = {}
        for start_node in self.nodes:
            self.__dijkstra(start_node)

    # list of edge
    def get_path(self, n1, n2):
        pass

    def get_path_length(self, n1, n2):
        return self.path_length[(n1, n2)]


    def __dijkstra(self, start_node):
        nodes_info = {node: info(node) for node in self.nodes}
        nodes_info[start_node].path_length = 0
        heap = []
        heappush(heap, nodes_info[start_node])
        while heap:
            curr_node_info = heappop(heap)
            curr_node_info.visited = True
            connect_nodes_info = {nodes_info[edge.lnode] if edge.rnode is curr_node_info.node else nodes_info[edge.rnode] for edge in curr_node_info.node.edges}
            for connect_node_info in connect_nodes_info:
                if connect_node_info.visited == False:
                    if connect_node_info.path_length > curr_node_info.path_length + 1:
                        connect_node_info.path_length = curr_node_info.path_length + 1
                        heappush(heap, connect_node_info)
        for node in self.nodes:
            if node is not start_node:
                self.path_length[(start_node, node)] = nodes_info[node].path_length

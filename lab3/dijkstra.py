from heapq import heappush, heappop

class info:
    def __init__(self, node):
        self.node = node
        self.visited = False
        self.path_length = float('inf')
    
    def __lt__(self, other_info):
        return self.path_length < other_info.path_length

class Dijkstra:

    def __init__(self, hosts, servers):
        self.nodes = hosts + servers
        self.parent_table = {}
        for start_node in hosts:
            self.parent_table[start_node] = {}
            self.__dijkstra(start_node)

    # list of edge
    def get_path(self, start_node, end_node):
        path = [end_node]
        parent = self.parent_table[start_node].get(end_node)
        while parent:
            path.insert(0, parent)
            parent = self.parent_table[start_node].get(parent)
        return path

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
                        self.parent_table[start_node][connect_node_info.node] = curr_node_info.node
                        heappush(heap, connect_node_info)

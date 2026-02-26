class Graph:
    """
    Graph (Adjacency List) to model relationships between mental health topics.
    Used to recommend related resources.
    """
    def __init__(self):
        self.adj_list = {}
        self.node_data = {} # Store metadata like "Title", "Description", "Link"

    def add_node(self, node_id: str, data: dict):
        if node_id not in self.adj_list:
            self.adj_list[node_id] = []
            self.node_data[node_id] = data

    def add_edge(self, u: str, v: str):
        """Undirected edge between related topics"""
        if u in self.adj_list and v in self.adj_list:
            self.adj_list[u].append(v)
            self.adj_list[v].append(u)

    def get_related(self, node_id: str):
        """Get all related topics for a given topic"""
        return [self.node_data[n] for n in self.adj_list.get(node_id, [])]

    def get_node(self, node_id: str):
        return self.node_data.get(node_id)

    def get_all_nodes(self):
        return self.node_data

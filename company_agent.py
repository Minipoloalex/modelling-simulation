from mesa import Agent
from graph_utils import get_closest_node

class CompanyAgent(Agent):
    def __init__(self, model, policy, location_position):
        super().__init__(model=model)
        self.location_position = location_position
        self.policy = policy        # Policy for this company (0 = no policy, 1 = full policy)
        self.location_nodes = {
            type: get_closest_node(graph, location_position)[0]
            for type, graph in self.model.graphs.items()
        }
        print(f"Company location nodes: {self.location_nodes}")

        self.visualization_node = self.location_nodes[self.model.visualization_graph_type]
        self.model.grid.place_agent(self, self.visualization_node)

    def step(self):
        # Update policy or provide incentives if needed
        pass  # More detailed behaviors could be added

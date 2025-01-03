from mesa import Agent
from graph_utils import get_closest_node


class CompanyAgent(Agent):
    def __init__(self, model, policy, location_position, company_budget):
        super().__init__(model=model)
        self.location_position = location_position
        self.workers = []
        self.policy = policy        # Policy for this company (0 = no policy, 1 = full policy)
        self.location_nodes = {
            type: get_closest_node(graph, location_position)[0]
            for type, graph in self.model.graphs.items()
        }
        self.total_cots_of_CO2_Kg = 0 # sum of all cost of pollution (CO2 Kg)
        self.company_budget = self.obtain_budget(company_budget)

        self.visualization_node = self.location_nodes[self.model.visualization_graph_type]
        self.model.grid.place_agent(self, self.visualization_node)

    def obtain_budget(self, company_budget):
        if self.policy == "policy3":
            return company_budget * 1.25
        elif self.policy == "policy4":
            return company_budget * 0.75
        return company_budget

    def add_worker(self, worker):
        self.workers.append(worker)

    def check_policies(self):
        sum_CO2kg = 0
        for agent in self.workers:
            sum_CO2kg += self.model.get_total_co2(agent)

        budget_diff_percent = (sum_CO2kg / self.company_budget - 1) * 100

        # Reference table for the sustainability factors
        factor_map = {
            10: 1.15,
            5: 1.08,
            0: 1.20,
            -5: 0.95,
            -10: 1.00,
            -100: 0.90  
        }

        # Find the factor in the table
        factor = factor_map.get(next((key for key in sorted(factor_map, reverse=True) if budget_diff_percent >= key), -100))

        for agent in self.workers:
            agent.modify_sustainable_factor(factor)

    def step(self):
        pass

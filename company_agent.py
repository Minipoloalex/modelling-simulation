from mesa import Agent
from graph_utils import get_closest_node

POSSIBLE_COMPANY_POLICIES = [f"policy{x}" for x in range(5)]

def obtain_budget(policy: str, company_budget: int) -> float:
    if policy == "policy3":
        return company_budget * 1.25
    elif policy == "policy4":
        return company_budget * 0.75
    return company_budget

class CompanyAgent(Agent):
    def __init__(self, model, policy: str, location_position: tuple[float, float], company_budget: int):
        super().__init__(model=model)
        self.location_position = location_position
        self.workers = []
        self.policy = policy
        self.location_nodes: dict[str, int] = {
            type: get_closest_node(graph, location_position)[0]
            for type, graph in self.model.graphs.items()
        }
        self.company_budget: float = obtain_budget(self.policy, company_budget)
        self.previous_sum_CO2: float = 0

        self.visualization_node = self.location_nodes[self.model.visualization_graph_type]
        self.model.grid.place_agent(self, self.visualization_node)


    def add_worker(self, worker):
        self.workers.append(worker)

    def check_policies(self):
        sum_CO2 = 0
        for agent in self.workers:
            sum_CO2 += self.model.get_total_co2(agent)

        curr_day_sum_CO2 = sum_CO2 - self.previous_sum_CO2
        budget_diff_percent = (curr_day_sum_CO2 / self.company_budget - 1) * 100

        # Reference table for the sustainability factors
        factor_map = {
            10: 1.20,
            5: 1.15,
            0: 1.08,
            -5: 0.95,
            -10: 1.00,
            -100: 0.90,
        }

        # Find the factor in the table
        factor = factor_map[
            next(
                (key for key in sorted(factor_map.keys(), reverse=True) if budget_diff_percent >= key),
                -100,
            )
        ]
        print(f"Budget diff %: {budget_diff_percent}, Factor {factor}")

        for agent in self.workers:
            agent.modify_sustainable_factor(factor)

        self.previous_sum_CO2 = sum_CO2

    def step(self):
        pass

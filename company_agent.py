from mesa import Agent
from graph_utils import get_closest_node

CAR_CO2_VALUE = 250
ESCOOTER_CO2_VALUE = 67

class CompanyAgent(Agent):
    def __init__(self, model, policy, location_position, BASE_COMPANY_BUDGET=  1000, workers = None):
        super().__init__(model=model)
        self.location_position = location_position
        self.workers = workers if workers is not None else []
        self.policy = policy        # Policy for this company (0 = no policy, 1 = full policy)
        self.location_nodes = {
            type: get_closest_node(graph, location_position)[0]
            for type, graph in self.model.graphs.items()
        }
        # print(f"Company location nodes: {self.location_nodes}")
        self.total_cots_of_CO2_Kg = 0 # sum of all cost of pollution (CO2 Kg)
        self.company_budget = BASE_COMPANY_BUDGET
        self.correct_budget()

        self.visualization_node = self.location_nodes[self.model.visualization_graph_type]
        self.model.grid.place_agent(self, self.visualization_node)

    def correct_budget(self):
        if self.policy == "policy3":
            self.company_budget *= 1.25
        elif self.policy == "policy4":
            self.company_budget *= 0.75

    def add_worker(self, worker):
        self.workers.append(worker)
        # Add a worker to this company
        pass

    def step(self):
        # Update policy or provide incentives if needed
        pass  # More detailed behaviors could be added
    
    def check_policies(self):
        sum_CO2kg = 0
        for agent in self.workers:
            sum_CO2kg += agent.kms_car[1] * CAR_CO2_VALUE + agent.kms_electric_scooter[1] * ESCOOTER_CO2_VALUE

        budget_diff_percent = (sum_CO2kg / self.company_budget - 1) * 100

        # Tabela de referência para os fatores de sustentabilidade
        factor_map = {
            10: 1.15,
            5: 1.08,
            0: 1.20,
            -5: 0.95,
            -10: 1.00,
            -100: 0.90  
        }

        # Encontrar o fator de sustentabilidade na tabela
        factor = factor_map.get(next((key for key in sorted(factor_map, reverse=True) if budget_diff_percent >= key), -100))

        for agent in self.workers:
            agent.modify_sustainable_factor(factor)
              

    def activate_policy(self):    
        if self.company_budget >= 0 :
            if self.policy == 'policy1' :
                self.policy1(self)
            elif self.policy == 'policy2':
                self.policy2(self)
        pass
    
    def policy1 (self):
        n_policy1 = 5               # number of workers to recibe a reward
        final_budget = self.BASE_COMPANY_BUDGET - self.total_cots_of_CO2_Kg
        reward = final_budget/n_policy1  # individual value of a reward to give the workers
        
        self.workers.sort(reverse=True, key=lambda worker: worker.daily_sustainable_score)
        
        for i in range(n_policy1):
            self.workers[i].sustainable_gain_sum += reward
        pass
    
    def policy2 (self):
        policy2_threshold = 100
        final_budget = self.BASE_COMPANY_BUDGET - self.total_cots_of_CO2_Kg
        reward = final_budget/self.num_of_workers  # individual value of a reward to give the workers
        
        workers = self.get_workers(self, policy2_threshold = policy2_threshold)
        
        for i in workers :
            i.sustainable_gain_sum += reward
        pass
                
    def get_workers(self, n_policy1 = -1, policy2_threshold = 0):
        
        all_workers = self.model.worker_agents
        company_workers = list
        
        for worker in all_workers :
            if worker.company == self and worker.daily_sustainable_score >= policy2_threshold :
                company_workers.append(worker)
            
        if n_policy1 > 0 :
            company_workers = self.get_top_company_workers(n_policy1,company_workers)
         
        return company_workers
    
    def get_top_company_workers(n_policy1, company_workers):
        top_company_workers = list
        company_workers.sort(reverse=True, key=lambda worker: worker.daily_sustainable_score)
            
        i = 0            
        for worker in company_workers :
            if i < n_policy1 :
                top_company_workers.append(worker)
                i += 1
        
        return top_company_workers
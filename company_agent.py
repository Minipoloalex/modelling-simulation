from mesa import Agent

# Define Company Agent
class CompanyAgent(Agent):
    BASE_COMPANY_BUDGET = 1000
    def __init__(self, unique_id, model, policy = 'base', num_of_workers = 0, BASE_COMPANY_BUDGET= 1000):
        self.unique_id = unique_id  # Manually set unique_id
        self.model = model          # Manually set model
        self.policy = policy        # Policy for this company ( 'base', 'policy1', 'policy2')
        self.num_of_workers = num_of_workers
        self.total_cots_of_CO2_Kg = 0 # sum of all cost of pollution (CO2 Kg)
        self.company_budget = BASE_COMPANY_BUDGET
        self.pos = None             # Initialize position attribute

    def step(self):
        # Update policy or provide incentives if needed
        pass  # More detailed behaviors could be added

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
        
        workers = self.get_workers(self, n_policy1 = n_policy1)
        
        for i in workers :
            i.sustainable_gain_sum += reward
        
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
        
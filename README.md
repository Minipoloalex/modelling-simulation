# Sustainable Transport Choices Simulation

## Problem Description
This project explores the impact of transport choices on sustainability through an agent-based simulation framework. It models the commuting behaviors of employees and evaluates how various factors—such as company policies, CO₂ budgets, and transport options—affect overall emissions and costs. Using real-world geographic data, the simulation allows for the analysis of scenarios with different sustainability strategies and provides insights into the effectiveness of credit schemes and other incentives.

**Key Features:**
- Agent-Based Simulation: Models workers and companies with individual behaviors and constraints.
- Scenario Analysis: Includes baseline and policy-driven scenarios to study sustainability impacts.
- Real-World Data: Uses geographic information to ensure realistic commuting patterns.
- Interactive Visualization: Enables dynamic exploration of parameters and results.

This repository contains the source code and documentation needed to replicate and extend the simulation.

## Set up and run the simulation model
After cloning the repository, you need to be in the root to follow the installation and how to run tutorial.
```bash
git clone git@github.com:Minipoloalex/modelling-simulation.git
cd modelling-simulation
```

First, to be able to run the simulation, you first need to install several Python packages. The simulation was developed and tested using **Python 3.12**


You can run the following code to install all the packages needed for the code.
```bash
pip install -r requirements.txt
```

To run the web app for the visualisation of the simulation model you can simply run this command in the shell:

```bash
solara run app.py
```

After opening the web app localhost page, there will be some controls to step through the simulation, and even some model parameters, so you can experiment with the model.

> Note: It may take a while to set up after running the command.

Using the visualisation, the simulation takes much longer to run. Therefore, to just run the simulation without the visualisation you can run the file `run.py`:


To check how to specify each model parameter here, just do:
```bash
python run.py --help
```

For example, you may run:
```bash
python run.py --num_workers_per_company 30 --policy0 3 --policy1 3
```

## Company policies
Here, we have the possible company policies we developed. Instead of naming them with a detailed description of what they represent, we decided to label them simply as indices of this table.

These can also be considered as the operation policies of our model and simulation.

| Policy | Budget | Modify Sustainability factor of employees | Init sustainability factor |
| :-:|:-:|:-:|:-:|
| 0 | x1 | X | 0 |
| 1 | x1 | X | 0.5 |
| 2 | x1 | Y | 0.5 |
| 3 | x1.4 | Y | 0.5 |
| 4 | x0.6 | Y | 0.5 |


## Developers:

- Félix Martins
- João Lima
- Pedro Azevedo

For more information, check the report [here](doc/Report.pdf) and the presentation [here](doc/Presentation.pdf).

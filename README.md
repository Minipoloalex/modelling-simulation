# Introduction

## Problem Formulation

Our project is based on an AYR credit scheme, where the main goal is to incentivise
more sustainable behaviours and to influence people to reduce their carbon footprint. The
group will create a simulation model and test it on a social simulation platform.
We will use a What-if analysis and two different models in order to build a valid,
coherent, and precise simulation. The two models we are going to use are:

- Prescriptive Model: In our project, we will study what transformations we can
make in order to improve our system. In our specific case, study the different credit
schemes or incentives that can be implemented by private companies in order to make
their employees more sustainable and reduce the overall carbon footprint.
- Speculative Model: This model will also be very important because we will use
different scenarios to test the new operation policies and different configurations of
our system and analyse them in terms of performance. Furthermore, the scenarios to
be simulated correspond to systems that do not exist yet.

The What-if analysis will also be crucial to our project. It will allow us to inspect the
behaviour of our complex system and assess how changes in a set of independent variables
(such as the scheme implemented by the companies) impact a set of dependent variables
(like transport usage or CO2 emissions).

## Problem description

Some companies are aiming to encourage their employees to adopt more sustainable
commuting habits by introducing a benefits or credit scheme designed to incentivise eco-
friendly travel choices

## Set up and run the simulation models

To be able to run the simulation, you first need access to several packages. In addition to the common packages, you also need the Mesa, OSMnx and Solara packages.

You can run the following code to install all the packages needed for the code.

`pip install -r requirements.txt`

To run the simulation models you can simply run the command:

`solara run app.py`


After opening the localhost page in the upper left corner there will be controls and model parameters.

> Note: It may take a while to set up after running the command.

**Enjoy!!!**

## Company policies

These can also be considered as the operation policies of our model and simulation.

| Policy | Budget | Modify Sustainability factor of employees | Init sustainability factor |
| :-:|:-:|:-:|:-:|
| 0 | x1 |X | 0 |
| 1 | x1 | X | 0.3 |
| 2 | x1 | Y | 0.3 |
| 3 | x1.25 | Y | 0.3|
| 4| x0.75 | Y | 0.3|


## Developers:

- Félix Martins
- João Lima
- Pedro Azevedo

For more information, check the report [here](doc/MS_CP1_WG_4.pdf).

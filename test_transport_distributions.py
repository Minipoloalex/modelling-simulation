import math
import random
import numpy as np
import matplotlib.pyplot as plt

def choose_transport(distances, sustainability_factor):
        transport_distance_car, additional_walk_distance_car = distances["drive"]
        transport_distance_walk, additional_walk_distance_walk = distances["walk"]
        transport_distance_eScooter, additional_walk_distance_eScooter = distances["bike"]
        transport_distance_bike, additional_walk_distance_bike = distances["bike"]
        # Dynamic adjustment functions based on distance
        def walking_probability(distance):
            # Walking becomes less likely as distance grows, near zero at >10 km
            return max(0, math.exp(-distance / 2))
        def bicycle_probability(distance):
            # Bicycling is more viable for mid distances, tapers off at longer distances
            return max(0, math.exp(-(distance - 5) ** 2 / 15))
        def electric_scooter_probability(distance):
            # Scooters are most viable for shorter distances, tapering off after ~8 km
            return max(0, math.exp(-(distance - 4) ** 2 / 8))
        def car_probability(distance):
            # Car becomes more likely as distance increases
            return min(1, distance / 10)
            
        dynamic_weights = {
            "car": car_probability(transport_distance_car + additional_walk_distance_car),
            "bike": bicycle_probability(transport_distance_bike + additional_walk_distance_bike),
            "electric_scooter": electric_scooter_probability(transport_distance_eScooter + additional_walk_distance_eScooter),
            "walk": walking_probability(transport_distance_walk + additional_walk_distance_walk)
        }
        # Sustainability bias
        dynamic_weights["bike"] *= 1 + sustainability_factor * 2
        dynamic_weights["walk"] *= 1 + sustainability_factor * 2
        dynamic_weights["electric_scooter"] *= 1 + sustainability_factor
        # Normalize weights to form a proper probability distribution
        total_weight = sum(dynamic_weights.values())
        if total_weight > 0:
            normalized_weights = {key: value / total_weight for key, value in dynamic_weights.items()}
        else:
            normalized_weights = {key: 0 for key in dynamic_weights}
        print(normalized_weights)
        transport_chosen = random.choices(
            list(normalized_weights.keys()),
            weights=list(normalized_weights.values()),
            k=1,
        )[0]
        return normalized_weights

# transport_probabilities = choose_transport({"drive": (12, 0), "walk": (7, 0), "bike": (8, 0)})
# print(transport_probabilities)

distances = np.linspace(0, 10, 100)
modes = ["car", "bike", "electric_scooter", "walk"]
types = ["drive", "bike", "walk"]

def plot_sustainability(sustainability, filename):
    probabilities = {mode: [] for mode in modes}
    # Calculate probabilities for each distance
    for distance in distances:
        params = {type: (distance, 0) for type in types}
        transport_probabilities = choose_transport(params, sustainability)
        for mode in modes:
            probabilities[mode].append(transport_probabilities[mode])

    # Plotting
    plt.figure(figsize=(10, 6))
    for mode in modes:
        plt.plot(distances, probabilities[mode], label=mode.capitalize())
    plt.title("Transport Probabilities vs Distance")
    plt.xlabel("Distance (km)")
    plt.ylabel("Probability")
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)

plot_sustainability(0, "0.png")
plot_sustainability(1, "1.png")

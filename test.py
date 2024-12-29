import math 
import random 

def choose_transport(distances):
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
            "bicycle": bicycle_probability(transport_distance_walk + additional_walk_distance_walk),
            "electric scooters": electric_scooter_probability(transport_distance_eScooter + additional_walk_distance_eScooter),
            "walking": walking_probability(transport_distance_bike + additional_walk_distance_bike)
        }

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

        return transport_chosen
                

transport_probabilities = choose_transport({"drive": (12, 0), "walk": (7, 0), "bike": (8, 0)})
print(transport_probabilities)
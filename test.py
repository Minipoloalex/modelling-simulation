import math 

def choose_transport(distance_to_work):

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
        "car": car_probability(distance_to_work),
        "bicycle": bicycle_probability(distance_to_work),
        "electric scooters": electric_scooter_probability(distance_to_work),
        "walking": walking_probability(distance_to_work)
    }

    # Normalize weights to form a proper probability distribution
    total_weight = sum(dynamic_weights.values())
    if total_weight > 0:
        normalized_weights = {key: value / total_weight for key, value in dynamic_weights.items()}
    else:
        normalized_weights = {key: 0 for key in dynamic_weights}

    return normalized_weights

transport_probabilities = choose_transport(9)
print(transport_probabilities)

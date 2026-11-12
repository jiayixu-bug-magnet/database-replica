# Order: skill_programming, skill_data_stats, skill_frontend_design, skill_business_pitch.
CENTROIDS = [
    [2.923076923076923, 3.0769230769230766, 2.8461538461538463, 4.0],
    [3.0, 3.6, 1.4, 1.5999999999999996],
    [4.2, 4.6, 4.0, 4.6],
]


def predict_cluster(skills):
    nearest = 0
    nearest_distance = None
    for cluster, centroid in enumerate(CENTROIDS):
        distance = 0.0
        for rating, center in zip(skills, centroid):
            gap = rating - center
            distance += gap * gap
        if nearest_distance is None or distance < nearest_distance:
            nearest = cluster
            nearest_distance = distance
    return nearest

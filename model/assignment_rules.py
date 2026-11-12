import csv

from cluster_model import predict_cluster

SKILL_COLUMNS = [
    "skill_programming",
    "skill_data_stats",
    "skill_frontend_design",
    "skill_business_pitch",
]


def assign_groups(students, n_groups=8):
    labeled = []
    for student in students:
        skills = [student[column] for column in SKILL_COLUMNS]
        labeled.append(
            {
                "id": student["id"],
                "cluster": predict_cluster(skills),
            }
        )

    counts = {}
    for student in labeled:
        cluster = student["cluster"]
        counts[cluster] = counts.get(cluster, 0) + 1

    # Largest cluster first. Equal sizes keep the lower cluster number first.
    cluster_order = sorted(counts, key=lambda cluster: (-counts[cluster], cluster))
    by_cluster = {cluster: [] for cluster in cluster_order}
    for student in labeled:
        by_cluster[student["cluster"]].append(student)
    for cluster in cluster_order:
        by_cluster[cluster].sort(key=lambda student: student["id"])

    deal = []
    for cluster in cluster_order:
        deal.extend(by_cluster[cluster])

    group_by_id = {}
    for index, student in enumerate(deal):
        group_by_id[student["id"]] = (index % n_groups) + 1

    return [
        {
            "id": student["id"],
            "cluster": student["cluster"],
            "group": group_by_id[student["id"]],
        }
        for student in labeled
    ]


def load_students(path):
    students = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            student = {"id": row["netid"]}
            for column in SKILL_COLUMNS:
                student[column] = int(row[column])
            students.append(student)
    return students


def main():
    assigned = assign_groups(load_students("class_dataset.csv"))
    clusters = sorted({student["cluster"] for student in assigned})
    missing = 0
    for group in range(1, 9):
        members = [student for student in assigned if student["group"] == group]
        present = {student["cluster"] for student in members}
        if present != set(clusters):
            missing += 1
        counts = ", ".join(
            f"cluster {cluster}: {sum(student['cluster'] == cluster for student in members)}"
            for cluster in clusters
        )
        print(f"group {group}: {len(members)} students, {counts}")
    print(f"groups missing a cluster: {missing}")


if __name__ == "__main__":
    main()

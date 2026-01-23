import random
import matplotlib.pyplot as plt

class Node:
    def __init__(self, x, y, energy=0.5):
        self.x = x
        self.y = y
        self.energy = energy
        self.isClusterHead = False
        self.cluster = None

class Cluster:
    def __init__(self, head):
        self.head = head
        self.nodes = [head]

    def add(self, node):
        if node not in self.nodes:
            self.nodes.append(node)

def leachSim(nodes, baseStation, rounds, p=0.1):
    for round in range(0, rounds):
        print(round)

if __name__ == '__main__':
    nodes = [Node(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(100)]
    plt.show()
    # print([random.uniform(0, 100) for _ in range(10)]);

    # print("Running LEACH Simulation...")
    # leachSim(nodes.copy(), base_station, rounds, 5)

    '''
    for round_num in range(num_rounds):
        # Step 1: Select cluster heads randomly based on probability p
        cluster_heads = [node for node in nodes if random.random() < p and node.is_alive()]
        clusters = []

        # Step 2: Form clusters with nodes assigned to the nearest cluster head
        for node in nodes:
            if node.is_alive() and node not in cluster_heads:
                nearest_cluster_head = min(cluster_heads, key=lambda ch: node.distance(ch))
                cluster = next((clu for clu in clusters if clu.cluster_head == nearest_cluster_head), None)
                if cluster is None:
                    cluster = Cluster(nearest_cluster_head)
                    clusters.append(cluster)
                cluster.add_node(node)

        # Step 3: Nodes send data to their respective cluster heads
        for cluster in clusters:
            energy_consumed = sum(node.distance(cluster.cluster_head) * 0.01 for node in cluster.nodes)
            for node in cluster.nodes:
                node.update_energy(energy_consumed)

        # Step 4: Base station receives data
        for cluster in clusters:
            base_station_energy_consumed = cluster.cluster_head.distance(base_station) * 0.02  # Cost for transmitting data to the base station
            cluster.cluster_head.update_energy(base_station_energy_consumed)

        # Remove dead nodes
        nodes = [node for node in nodes if node.is_alive()]
        
        print(f"Round {round_num + 1}: {len(nodes)} nodes alive")

    return nodes
    '''

def leach_e_simulation(nodes, base_station, num_rounds=100):
    for round_num in range(num_rounds):
        # Step 1: Select cluster heads based on energy level
        cluster_heads = [node for node in nodes if node.is_alive()]
        cluster_heads.sort(key=lambda x: x.energy, reverse=True)
        cluster_heads = cluster_heads[:len(nodes) // 5]  # Select top 20% based on energy

        clusters = []
        for node in nodes:
            if node.is_alive() and node not in cluster_heads:
                nearest_cluster_head = min(cluster_heads, key=lambda ch: node.distance(ch))
                cluster = next((clu for clu in clusters if clu.cluster_head == nearest_cluster_head), None)
                if cluster is None:
                    cluster = Cluster(nearest_cluster_head)
                    clusters.append(cluster)
                cluster.add_node(node)

        # Step 2: Communication to cluster head and base station
        for cluster in clusters:
            energy_consumed = sum(node.distance(cluster.cluster_head) * 0.01 for node in cluster.nodes)
            for node in cluster.nodes:
                node.update_energy(energy_consumed)

        for cluster in clusters:
            base_station_energy_consumed = cluster.cluster_head.distance(base_station) * 0.02
            cluster.cluster_head.update_energy(base_station_energy_consumed)

        nodes = [node for node in nodes if node.is_alive()]
        
        print(f"Round {round_num + 1}: {len(nodes)} nodes alive")

    return nodes


def leach_c_simulation(nodes, base_station, num_rounds=100):
    for round_num in range(num_rounds):
        # Step 1: Base station selects cluster heads based on residual energy and distance to base station
        nodes_sorted = sorted(nodes, key=lambda node: node.energy, reverse=True)
        cluster_heads = nodes_sorted[:len(nodes) // 5]  # Select top 20% nodes as cluster heads
        clusters = []

        # Step 2: Assign nodes to cluster heads based on distance
        for node in nodes:
            if node.is_alive() and node not in cluster_heads:
                nearest_cluster_head = min(cluster_heads, key=lambda ch: node.distance(ch))
                cluster = next((clu for clu in clusters if clu.cluster_head == nearest_cluster_head), None)
                if cluster is None:
                    cluster = Cluster(nearest_cluster_head)
                    clusters.append(cluster)
                cluster.add_node(node)

        # Step 3: Communication to cluster head and base station
        for cluster in clusters:
            energy_consumed = sum(node.distance(cluster.cluster_head) * 0.01 for node in cluster.nodes)
            for node in cluster.nodes:
                node.update_energy(energy_consumed)

        for cluster in clusters:
            base_station_energy_consumed = cluster.cluster_head.distance(base_station) * 0.02
            cluster.cluster_head.update_energy(base_station_energy_consumed)

        nodes = [node for node in nodes if node.is_alive()]

        print(f"Round {round_num + 1}: {len(nodes)} nodes alive")

    return nodes



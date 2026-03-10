import random
import math

CTRL_PACKET_SIZE = 200 # bits for control packets (ADV, JOIN, TDMA, etc)

class LEACH_GA:
    """
    LEACH-GA (Genetic Algorithm based LEACH).
    Uses a centralized approach during the setup phase where a GA optimizes
    cluster head selection by maximizing residual energy and minimizing distances.
    """
    def __init__(self, network, p=0.05, pop_size=30, generations=20):
        self.network = network
        self.p = p
        self.pop_size = pop_size
        self.generations = generations
        
    def _evaluate_fitness(self, chromosome, active_nodes):
        """
        Fitness Function for a specific chromosome (set of CHs).
        chromosome: Boolean list representing if a node is CH or not.
        Objectives:
        1. Minimize distance from members to their CHs.
        2. Maximize residual energy of CHs.
        3. Penalty if number of CHs is not close to optimal (k_opt = N * p).
        """
        chs = [node for idx, node in enumerate(active_nodes) if chromosome[idx]]
        members = [node for idx, node in enumerate(active_nodes) if not chromosome[idx]]
        
        # Penalty for 0 CHs (invalid state)
        if not chs:
            return -float('inf')
            
        # 1. Distance cost (sum of squared distances from member to nearest CH)
        dist_cost = 0
        for member in members:
            min_dist = min([member.calculate_distance(ch) for ch in chs])
            dist_cost += min_dist ** 2
            
        # 2. Energy cost (bottleneck energy of chosen CHs)
        min_energy = min([ch.energy for ch in chs])
        
        # Normalize distance (rough approximation preventing explosion)
        k_opt = max(1, math.ceil(len(active_nodes) * self.p))
        k_penalty = abs(len(chs) - k_opt) * 1000 # Heavy penalty for deviating from optimal cluster count
        
        # Fitness: Maximize bottleneck energy, Minimize distance and penalty
        fitness = (min_energy * 100000) - dist_cost - k_penalty
        return fitness
        
    def _run_ga(self, active_nodes):
        """Runs the Genetic Algorithm to find the best CH set."""
        num_nodes = len(active_nodes)
        
        if num_nodes < 2:
            return active_nodes
            
        k_opt = max(1, math.ceil(num_nodes * self.p))
        
        # 1. Initialize population
        population = []
        for _ in range(self.pop_size):
            # Random chromosome with ~k_opt 1s
            chrom = [False] * num_nodes
            ch_indices = random.sample(range(num_nodes), min(num_nodes, k_opt))
            for idx in ch_indices:
                chrom[idx] = True
            population.append(chrom)
            
        best_overall = None
        best_fitness = -float('inf')
        
        for _ in range(self.generations):
            # Evaluate fitness
            evaluated = []
            for chrom in population:
                fit = self._evaluate_fitness(chrom, active_nodes)
                evaluated.append((chrom, fit))
                if fit > best_fitness:
                    best_fitness = fit
                    best_overall = chrom
                    
            # Tournament selection
            evaluated.sort(key=lambda x: x[1], reverse=True)
            parents = [x[0] for x in evaluated[:self.pop_size // 2]]
            
            # Crossover & Mutation
            next_generation = parents.copy()
            while len(next_generation) < self.pop_size:
                p1, p2 = random.sample(parents, 2)
                # Single point crossover
                c_point = random.randint(1, num_nodes - 1)
                child = p1[:c_point] + p2[c_point:]
                
                # Mutation (flip 1 bit with small prob)
                if random.random() < 0.1:
                    m_point = random.randint(0, num_nodes - 1)
                    child[m_point] = not child[m_point]
                    
                next_generation.append(child)
                
            population = next_generation
            
        # Extract best CHs
        return [active_nodes[i] for i in range(num_nodes) if best_overall[i]]

    def run_round(self):
        self.network.round_num += 1
        alive_nodes = self.network.get_alive_nodes()
        if not alive_nodes:
            self.network.save_network_state(0, 0)
            return 0
        
        readings = self.network.get_data_for_round(alive_nodes)
        
        active_nodes = [n for n in alive_nodes if n.id in readings]
        sleeping_nodes = [n for n in alive_nodes if n.id not in readings]
        
        energy_this_round = 0
        for node in sleeping_nodes:
            energy_this_round += self.network.consume_node_energy(node, 'sleep')
            node.type = 'sleeping'
            node.cluster = None

        if not active_nodes:
            self.network.save_network_state(energy_this_round, 0)
            return energy_this_round
            
        # 1. Setup Phase: BS selects CHs via GA
        # Nodes send info to BS
        for node in active_nodes:
            energy_this_round += self.network.consume_node_energy(node, 'tx', distance=node.distance_to_bs, bits=CTRL_PACKET_SIZE)
            
        # Run genetic algorithm to find CHs
        chs = self._run_ga(active_nodes)
        if not chs: # Failsafe
            chs = [random.choice(active_nodes)]
            
        for node in active_nodes:
            node.type = 'normal'
            node.cluster = None
            
        for ch in chs:
            ch.type = 'ch'
            
        members = [node for node in active_nodes if node.type == 'normal']
        
        # 2. Cluster Formation
        for node in members:
            min_dist = float('inf')
            nearest_ch = None
            for ch in chs:
                dist = node.calculate_distance(ch)
                if dist < min_dist:
                    min_dist = dist
                    nearest_ch = ch
            node.cluster = nearest_ch

        # BS broadcasts CH assignments
        for node in active_nodes:
            energy_this_round += self.network.consume_node_energy(node, 'rx', bits=CTRL_PACKET_SIZE)

        # 3. Steady-State Phase
        ch_member_counts = {ch.id: 0 for ch in chs}

        # Members to CHs
        for node in members:
            if node.cluster:
                dist = node.calculate_distance(node.cluster)
                energy_this_round += self.network.consume_node_energy(node, 'tx', distance=dist)
                energy_this_round += self.network.consume_node_energy(node.cluster, 'rx')
                ch_member_counts[node.cluster.id] += 1
            
        # CHs to BS
        throughput_round = len(active_nodes)
        for ch in chs:
            num_signals = ch_member_counts.get(ch.id, 0) + 1
            energy_this_round += self.network.consume_node_energy(ch, 'fusion', num_signals=num_signals)
            energy_this_round += self.network.consume_node_energy(ch, 'tx', distance=ch.distance_to_bs)
            
        self.network.save_network_state(energy_this_round, throughput_round)
        return energy_this_round

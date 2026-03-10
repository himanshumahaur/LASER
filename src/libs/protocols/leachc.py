import random
import math

CTRL_PACKET_SIZE = 200 # bits for control packets (ADV, JOIN, TDMA, etc)

class LEACHC:
    def __init__(self, network, p=0.05):
        self.network = network
        self.p = p
        
    def run_round(self):
        self.network.round_num += 1
        alive_nodes = self.network.get_alive_nodes()
        if not alive_nodes:
            self.network.save_network_state(0, 0)
            return 0
        
        # Pull sensor readings for this round
        readings = self.network.get_data_for_round(alive_nodes)
        
        # Identify active and sleeping nodes
        active_nodes = [n for n in alive_nodes if n.id in readings]
        sleeping_nodes = [n for n in alive_nodes if n.id not in readings]
        
        # Energy for sleeping nodes
        energy_this_round = 0
        for node in sleeping_nodes:
            energy_this_round += self.network.consume_node_energy(node, 'sleep')
            node.type = 'sleeping'
            node.cluster = None

        if not active_nodes:
            self.network.save_network_state(energy_this_round, 0)
            return energy_this_round
            
        # 1. Setup Phase: Centralized BS Selection
        # All nodes send their current location and energy level to BS
        for node in active_nodes:
            energy_this_round += self.network.consume_node_energy(node, 'tx', distance=node.distance_to_bs, bits=CTRL_PACKET_SIZE)
            
        # BS calculates max and avg energy
        avg_energy = sum([node.energy for node in active_nodes]) / len(active_nodes)
        
        # Candidates: Nodes with energy >= average
        candidates = [node for node in active_nodes if node.energy >= avg_energy]
        if not candidates:
            candidates = active_nodes.copy()
            
        # Ensure we have enough CHs (use ceil to avoid too few clusters)
        num_chs = max(1, math.ceil(len(active_nodes) * self.p))
        
        chs = []
        # Greedy Optimization (Simulated Annealing approximation)
        if candidates:
            best_cost = float('inf')
            best_chs = []
            
            # Random Search for best CH set that minimizes squared distance
            num_trials = 50
            for _ in range(num_trials):
                if len(candidates) >= num_chs:
                    trial_chs = random.sample(candidates, num_chs)
                else:
                    trial_chs = candidates.copy()
                    
                cost = 0
                for n in active_nodes:
                    min_dist = min([n.calculate_distance(ch) for ch in trial_chs])
                    # Square distance to heavily penalize nodes too far from nearest CH
                    cost += min_dist ** 2 
                    
                if cost < best_cost:
                    best_cost = cost
                    best_chs = trial_chs
                    
            chs = best_chs

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

        # BS broadcasts the CH assignment to all nodes
        # Approximating: all nodes receive the broadcast schedule
        for node in active_nodes:
            energy_this_round += self.network.consume_node_energy(node, 'rx', bits=CTRL_PACKET_SIZE)

        # 3. Steady-State Phase: Energy Consumption
        ch_member_counts = {ch.id: 0 for ch in chs}

        # Members to CHs
        for node in members:
            if node.cluster:
                dist = node.calculate_distance(node.cluster)
                energy_this_round += self.network.consume_node_energy(node, 'tx', distance=dist)
                energy_this_round += self.network.consume_node_energy(node.cluster, 'rx')
                ch_member_counts[node.cluster.id] += 1
            
        # CHs to BS
        throughput_round = len(active_nodes) # Represents number of sensor readings delivered
        for ch in chs:
            num_signals = ch_member_counts.get(ch.id, 0) + 1
            energy_this_round += self.network.consume_node_energy(ch, 'fusion', num_signals=num_signals)
            energy_this_round += self.network.consume_node_energy(ch, 'tx', distance=ch.distance_to_bs)
            
        self.network.save_network_state(energy_this_round, throughput_round)
        return energy_this_round

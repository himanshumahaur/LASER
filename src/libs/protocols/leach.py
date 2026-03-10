import random

CTRL_PACKET_SIZE = 200 # bits for control packets (ADV, JOIN, TDMA, etc)

class LEACH:
    def __init__(self, network, p=0.05):
        self.network = network
        self.p = p # Probability of becoming cluster head
        self.was_ch = set() # Nodes that were CHs in the current cycle
        
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
            
        # Reset CH cycle
        cycle_len = int(1/self.p)
        # Round num is 1-indexed. Cycle ends when (round - 1) % cycle_len == 0
        if (self.network.round_num - 1) % cycle_len == 0:
            self.was_ch = set()
            
        chs = []
        members = []
        
        # 1. Setup Phase: Cluster Head Selection
        for node in active_nodes:
            node.type = 'normal'
            node.cluster = None
            
            if node.id in self.was_ch:
                members.append(node)
                continue
                
            # Current cycle round index: 0 to cycle_len-1
            r_cycle = (self.network.round_num - 1) % cycle_len
            threshold = self.p / (1 - self.p * r_cycle)
            
            if random.random() <= threshold:
                node.type = 'ch'
                chs.append(node)
                self.was_ch.add(node.id)
            else:
                members.append(node)
                
        # Fallback if no CH selected
        if not chs and active_nodes:
            # If no CH is selected, all nodes must transmit directly to the BS (huge penalty)
            for node in active_nodes:
                energy_this_round += self.network.consume_node_energy(node, 'tx', distance=node.distance_to_bs)
            self.network.save_network_state(energy_this_round, len(active_nodes))
            return energy_this_round
                
        # Setup Phase: Overhead
        # CHs broadcast ADV. Members receive ADV from each CH.
        for ch in chs:
            # Broadcast ADV (max distance of network bounds ~100m)
            energy_this_round += self.network.consume_node_energy(ch, 'tx', distance=100, bits=CTRL_PACKET_SIZE) 
            # Members receive the ADV
            for member in members:
                energy_this_round += self.network.consume_node_energy(member, 'rx', bits=CTRL_PACKET_SIZE)

        # 2. Cluster Formation
        for node in members:
            # Find nearest CH based on signal strength (distance)
            min_dist = float('inf')
            nearest_ch = None
            for ch in chs:
                dist = node.calculate_distance(ch)
                if dist < min_dist:
                    min_dist = dist
                    nearest_ch = ch
            node.cluster = nearest_ch
            
            # Member sends JOIN request
            energy_this_round += self.network.consume_node_energy(node, 'tx', distance=min_dist, bits=CTRL_PACKET_SIZE)
            # CH receives JOIN request
            if nearest_ch:
                energy_this_round += self.network.consume_node_energy(nearest_ch, 'rx', bits=CTRL_PACKET_SIZE)
        
        # Setup Phase: CH creates and transmits TDMA schedule
        for ch in chs:
            # Broadcast TDMA
            energy_this_round += self.network.consume_node_energy(ch, 'tx', distance=100, bits=CTRL_PACKET_SIZE)
            
        for member in members:
            # Receive TDMA
            if member.cluster:
                energy_this_round += self.network.consume_node_energy(member, 'rx', bits=CTRL_PACKET_SIZE)

        # 3. Steady-State Phase: Data Transmission and Energy Consumption
        ch_member_counts = {ch.id: 0 for ch in chs}
        
        # Members send data to CHs
        for node in members:
            if node.cluster:
                dist = node.calculate_distance(node.cluster)
                # Tx data
                energy_this_round += self.network.consume_node_energy(node, 'tx', distance=dist)
                # CH Rx data
                energy_this_round += self.network.consume_node_energy(node.cluster, 'rx')
                ch_member_counts[node.cluster.id] += 1
            
        # CHs aggregate and send to BS
        throughput_round = len(active_nodes) # Each CH sends one aggregated packet, meaning all active nodes were delivered
        for ch in chs:
            # Aggregate data (Received signals + its own sensing data)
            num_signals = ch_member_counts.get(ch.id, 0) + 1
            energy_this_round += self.network.consume_node_energy(ch, 'fusion', num_signals=num_signals)
            
            # Send to BS
            energy_this_round += self.network.consume_node_energy(ch, 'tx', distance=ch.distance_to_bs)
            
        self.network.save_network_state(energy_this_round, throughput_round)
        return energy_this_round

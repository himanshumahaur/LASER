import random

CTRL_PACKET_SIZE = 200 # bids for control

class PEGASIS:
    """
    PEGASIS (Power-Efficient Gathering in Sensor Information Systems).
    A chain-based protocol where nodes only communicate with their closest neighbors.
    One leader node per round transmits to the BS.
    """
    def __init__(self, network, current_leader=None):
        self.network = network
        self.current_leader = current_leader
        self.chain = []
        
    def _form_chain(self, active_nodes):
        """Forms a chain using a greedy algorithm based on distance."""
        unvisited = set(active_nodes)
        if not unvisited:
            return []
            
        # Start at node furthest from BS
        start_node = max(unvisited, key=lambda n: n.distance_to_bs)
        unvisited.remove(start_node)
        
        chain = [start_node]
        current_node = start_node
        
        while unvisited:
            # Find nearest unvisited neighbor
            nearest = min(unvisited, key=lambda n: current_node.calculate_distance(n))
            chain.append(nearest)
            unvisited.remove(nearest)
            current_node = nearest
            
        return chain

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
            
        # Optional: Reform chain if nodes die
        # Since active_nodes can change per epoch, we reform the chain for active sensors only if needed.
        if len(self.chain) != len(active_nodes) or not all(n in self.chain for n in active_nodes):
            self.chain = self._form_chain(active_nodes)
            # Setup Phase: Token passing/Synchronization overhead for the chain 
            # (approximate as 1 tx/rx per node) - ONLY happens when chain is reformed
            for i in range(len(self.chain) - 1):
                n1, n2 = self.chain[i], self.chain[i+1]
                dist = n1.calculate_distance(n2)
                energy_this_round += self.network.consume_node_energy(n1, 'tx', distance=dist, bits=CTRL_PACKET_SIZE)
                energy_this_round += self.network.consume_node_energy(n2, 'rx', bits=CTRL_PACKET_SIZE)
        
        # Select Leader (Round-Robin along the chain)
        # Round 1 -> index 0, Round 2 -> index 1, etc.
        leader_index = (self.network.round_num - 1) % len(self.chain)
        leader = self.chain[leader_index]
        
        for node in active_nodes:
            node.type = 'normal'
            node.cluster = None
        leader.type = 'ch' # Mark as leader for visualization/tracking
            
        # 2. Steady-State Phase (Data transmission along the chain)
        # Data moves from ends of the chain towards the leader
        left_chain = self.chain[:leader_index]
        right_chain = self.chain[leader_index+1:][::-1] # Reverse right side
        
        # Process left side (moves right towards leader)
        signals = 1 # Node's own reading
        for i in range(len(left_chain)):
            node = left_chain[i]
            target = left_chain[i+1] if i < len(left_chain)-1 else leader
            dist = node.calculate_distance(target)
            
            # Fuse data (if it received from previous)
            if signals > 1:
               energy_this_round += self.network.consume_node_energy(node, 'fusion', num_signals=signals)
               
            energy_this_round += self.network.consume_node_energy(node, 'tx', distance=dist)
            energy_this_round += self.network.consume_node_energy(target, 'rx')
            # In PEGASIS, data is fully aggregated at each hop. Meaning signal count resets to 2 
            # (1 from previous + 1 own).
            signals = 2 
            
        leader_signals_left = signals if left_chain else 1

        # Process right side (moves left towards leader)
        signals = 1
        for i in range(len(right_chain)):
            node = right_chain[i]
            target = right_chain[i+1] if i < len(right_chain)-1 else leader
            dist = node.calculate_distance(target)
            
            if signals > 1:
               energy_this_round += self.network.consume_node_energy(node, 'fusion', num_signals=signals)
               
            energy_this_round += self.network.consume_node_energy(node, 'tx', distance=dist)
            energy_this_round += self.network.consume_node_energy(target, 'rx')
            signals = 2
            
        leader_signals_right = signals if right_chain else 1
        
        # Leader aggregates and sends to BS
        total_signals_to_fuse = leader_signals_left + leader_signals_right - 1 # -1 since leader's own reading counted twice if both chains exist
        if not left_chain and not right_chain:
            total_signals_to_fuse = 1
            
        if total_signals_to_fuse > 1:
            energy_this_round += self.network.consume_node_energy(leader, 'fusion', num_signals=total_signals_to_fuse)
            
        energy_this_round += self.network.consume_node_energy(leader, 'tx', distance=leader.distance_to_bs)
        
        throughput_round = len(active_nodes)
        self.network.save_network_state(energy_this_round, throughput_round)
        return energy_this_round

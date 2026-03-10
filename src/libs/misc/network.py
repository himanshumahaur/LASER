import math
from libs.misc.energy_model import EnergyModel

# Initialize Energy Model
model = EnergyModel()

ENERGY_INIT = 0.5       # 0.5 Joules (classical testbench)
BLOCK_SIZE = 4000       # 4000 bits per message

class Node:
    def __init__(self, id, x, y, energy=ENERGY_INIT, readings=None):
        self.id = id
        self.x = x
        self.y = y
        self.initial_energy = energy
        self.energy = energy
        self.is_alive = True
        self.distance_to_bs = 0
        self.type = 'normal' # 'normal' or 'ch' (Cluster Head) or 'relay' or 'sleeping'
        self.cluster = None
        self.history = {} # round_num -> {energy, is_alive, type, cluster_id}
        self.readings = readings if readings else {} # epoch -> reading_dict

    def reset(self):
        """Resets the node to its initial state."""
        self.energy = self.initial_energy
        self.is_alive = True
        self.type = 'normal'
        self.cluster = None
        self.history = {}

    def get_reading_at_epoch(self, epoch):
        """Returns the sensor reading for this node at a specific epoch."""
        reading = self.readings.get(epoch)
        if reading:
            result = reading.copy()
            result['moteid'] = self.id
            result['epoch'] = epoch
            return result
        return None

    def calculate_distance(self, other_node):
        return math.sqrt((self.x - other_node.x)**2 + (self.y - other_node.y)**2)

    def calculate_distance_to_point(self, x, y):
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)

    def consume_energy(self, amount):
        if self.is_alive:
            self.energy -= amount
            if self.energy <= 0:
                self.energy = 0
                self.is_alive = False
                return True
        return False
    
    def save_round_state(self, round_num):
        """Stores node-level information for the given round."""
        self.history[round_num] = {
            'energy': self.energy,
            'is_alive': self.is_alive,
            'type': self.type,
            'cluster_id': self.cluster.id if self.cluster else None
        }

def calculate_tx_energy(bits, distance):
    return model.tx_energy(bits, distance)

def calculate_rx_energy(bits):
    return model.rx_energy(bits)

def calculate_fusion_energy(bits, num_signals=1):
    return model.fusion_energy(bits, num_signals)

def calculate_sleep_energy(bits):
    return model.sleep_energy(bits)

class Network:
    def __init__(self, sensor_reader, bs_location=(25, 100)):
        self.reader = sensor_reader
        self.bs_x, self.bs_y = bs_location
        self.nodes = []
        self._initialize_nodes()
        self.round_num = 0
        self.cumulative_throughput = 0
        self.history = {} # round_num -> {alive_nodes, dead_nodes, total_energy, ...}

    def _initialize_nodes(self):
        mote_locs = self.reader.get_mote_locations()

        for node_id, (x, y) in mote_locs.items():
            readings = self.reader.get_node_data(node_id)
            node = Node(node_id, x, y, readings=readings)
            node.distance_to_bs = node.calculate_distance_to_point(self.bs_x, self.bs_y)
            self.nodes.append(node)
        
        # After initialization, the reader is no longer needed
        self.reader = None

    def reset(self):
        """Resets the network and all nodes to initial state."""
        self.round_num = 0
        self.cumulative_throughput = 0
        self.history = {}
        for node in self.nodes:
            node.reset()
            
    def get_alive_nodes(self):
        return [node for node in self.nodes if node.is_alive]

    def get_data_for_round(self, alive_nodes):
        """Pulls sensor reading for each node for the CURRENT epoch/round."""
        readings = {}
        for node in alive_nodes:
            # Nodes now store their own data
            reading = node.get_reading_at_epoch(self.round_num)
            if reading:
                readings[node.id] = reading
        return readings

    def record_round_stats(self, energy_consumed_round, throughput_round):
        """Stores network-level and node-level information for the given round."""
        alive_nodes = self.get_alive_nodes()
        num_alive = len(alive_nodes)
        num_dead = len(self.nodes) - num_alive
        residual_energy = sum(node.energy for node in self.nodes)
        self.cumulative_throughput += throughput_round
        
        self.history[self.round_num] = {
            'round': self.round_num,
            'alive_nodes': num_alive,
            'dead_nodes': num_dead,
            'residual_energy': round(residual_energy, 6),
            'energy_consumed_round': round(energy_consumed_round, 6),
            'throughput_round': throughput_round,
            'cumulative_throughput': self.cumulative_throughput
        }
        
    def consume_node_energy(self, node, operation, **kwargs):
        """
        Decrements energy from a node based on the type of operation.
        Supported operations: 'tx', 'rx', 'fusion', 'sleep'
        """
        if not node.is_alive:
            return 0
            
        energy = 0
        bits = kwargs.get('bits', BLOCK_SIZE)
        
        if operation == 'tx':
            distance = kwargs.get('distance', 0)
            energy = calculate_tx_energy(bits, distance)
        elif operation == 'rx':
            energy = calculate_rx_energy(bits)
        elif operation == 'fusion':
            num_signals = kwargs.get('num_signals', 1)
            energy = calculate_fusion_energy(bits, num_signals)
        elif operation == 'sleep':
            energy = calculate_sleep_energy(bits)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
        node.consume_energy(energy)
        return energy

    def save_network_state(self, energy_consumed_round, throughput_round):
        """Saves current round state for network and all nodes."""
        self.record_round_stats(energy_consumed_round, throughput_round)
        for node in self.nodes:
            node.save_round_state(self.round_num)

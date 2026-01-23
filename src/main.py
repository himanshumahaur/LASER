class Node:
    def __init__(self, id, battery = 100):
        self.id = id
        self.battery = battery

    def tick(self):
        print('tick')

class Network:
    def __init__(self, nodes):
        self.nodes = nodes

    def tick(self):
        for node in self.nodes:
            node.tick()

class NetworkUtils:
    def createNetwork(self, nodes):
        network = Network(nodes)
        return network

if __name__ == '__main__':
    n1 = Node(1)
    n2 = Node(2)
    n3 = Node(3)

    net1 = Network([n1, n2, n3])
    net1.tick()

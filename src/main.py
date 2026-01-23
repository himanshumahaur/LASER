class Node:
    def __init__(self, id, x, y, energy):
        self.id = id
        self.x = x
        self.y = y
        self.energy = energy

        self.isCH = False
        self.cluster = None

class Network:
    def __init__(self, nodes):
        self.nodes = nodes


if __name__ == '__main__':
    print('LASER')

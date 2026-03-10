# LASER [WORK IN PROGRESS]

## Supported Protocols

1. **PEGASIS**: Chain-based data routing protocol where each node communicates only with a close neighbor and takes turns transmitting to the Base Station.
2. **LEACH-GA**: Genetic Algorithm-based wrapper to optimally choose Cluster Heads (CHs) based on bottleneck residual energy and intra-cluster distances to the CHs.
3. **LEACH-C**: Centralized LEACH protocol where the Base Station selects CHs using an optimization approach to balance energy consumption.
4. **LEACH**: The classical distributed routing protocol with randomized CH rotation.

## Features

- **Energy Model**: Utilizes standard classical literature parameters (from the First Order Radio Model, such as `ENERGY_INIT = 0.5J`).
- **Multipath Fading & Distance Penalties**: The Base Station is positioned far outside the network to correctly model distance-based energy drain.

## Installation & Usage

1. **Requirements:**
   ```bash
   pip install pandas matplotlib numpy
   ```

2. **Run the simulation:**
   ```bash
   python src/main.py
   ```

## Simulation Results Benchmarking

(**PEGASIS > LEACH-C > LEACH-GA > LEACH**):

1. **PEGASIS**: Showcases the highest network longevity. By distributing the transmission burden equally via a nearest-neighbor chain, it sustains operations far longer than clustered equivalents before dropping to 1 node.
2. **LEACH-C**: Centralized selection heavily protects nodes with below-average energy, keeping almost all nodes homogeneously alive until a synchronized mass-death around round 800.
3. **LEACH-GA**: Outperforms localized LEACH but generally underperforms centralized LEACH-C/PEGASIS. It balances distances effectively but genetic operations can slightly favor node clustering variance over pure longevity.
4. **LEACH**: Performs the worst. Due to rapid energy drain on poorly-located randomized Cluster Heads transmitting to a distant Base Station, the network fractures early.

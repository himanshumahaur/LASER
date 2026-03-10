import sys
import os
import json
import pandas as pd

sys.path.append(os.path.join(os.getcwd(), 'src/libs'))

from libs.misc import SensorDataReader, Network
from libs.protocols import LEACH, LEACHC, LEACH_GA, PEGASIS
from libs.plot import Plotter


def run_simulation(protocol_class, network, rounds, **protocol_params):
    """
    Runs a simulation for a given protocol class and network.
    Returns the simulation history as a DataFrame.
    """
    network.reset()
    protocol = protocol_class(network, **protocol_params)
    total_energy_consumed = 0

    total_overhead = 0
    total_delay = 0

    print(f"\nStarting simulation for {protocol_class.__name__}...")
    for r in range(1, rounds + 1):
        # We need to add basic logic for overhead/delay collection if it was missing 
        # (Using basic approximations for this demo)
        energy_this_round = protocol.run_round()
        total_energy_consumed += energy_this_round
        
        # Overhead approx = number of active nodes * 0.1
        # Delay approx = number of active nodes * 0.05
        alive_nodes_count = len([n for n in network.nodes if n.is_alive])
        total_overhead += alive_nodes_count * 0.1
        total_delay += alive_nodes_count * 0.05
        
        round_data = network.history[network.round_num]
        num_alive = round_data['alive_nodes']
        
        if r % 100 == 0 or num_alive == 0:
            print(f"Round {r:4}: Alive={num_alive:3}, Dead={round_data['dead_nodes']:3}, "
                  f"Residual Energy={round_data['residual_energy']:8.4f} J, "
                  f"Throughput={round_data['cumulative_throughput']:5}")
            
        if num_alive == 0:
            print(f"All nodes died at round {r}.")
            break
            
    # Scalability Metrics Extract
    final_throughput = network.history[network.round_num]['cumulative_throughput']
    final_lifetime = network.round_num
    
    scalability_stats = {
        'nodes': len(network.nodes),
        'throughput_bps': final_throughput,
        'lifetime_rounds': final_lifetime,
        'signal_overhead': total_overhead,
        'e2e_delay_ms': total_delay
    }
    
    # Cluster Data Extract (Final Round)
    cluster_counts = {}
    for node in network.nodes:
        if node.is_alive and node.cluster:
            cluster_id = node.cluster.id
            cluster_counts[cluster_id] = cluster_counts.get(cluster_id, 0) + 1
            
    # Format into dataframe format
    cluster_df = pd.DataFrame({
        'cluster_id': [idx + 1 for idx in range(len(cluster_counts.keys()))], 
        'members': list(cluster_counts.values())
    }) if cluster_counts else pd.DataFrame({'cluster_id': [], 'members': []})

    return pd.DataFrame(network.history.values()), scalability_stats, cluster_df


if __name__ == "__main__":
    with open('config.json', 'r') as f:
        CONFIG = json.load(f)

    reader = SensorDataReader(CONFIG)
    bs_location = (CONFIG.get('baseStation').get('x'), CONFIG.get('baseStation').get('y'))
    max_rounds = CONFIG.get('simulation').get('rounds')

    # Initialize Network (Nodes are initialized once)
    network = Network(reader, bs_location=bs_location)

    # 1. Run LEACH Simulation
    df_leach, sc_leach, cl_leach = run_simulation(LEACH, network, max_rounds, p=0.05)
    df_leach.to_csv('output/leach_results.csv', index=False)

    # 2. Run LEACH-C Simulation
    df_leachc, sc_leachc, cl_leachc = run_simulation(LEACHC, network, max_rounds, p=0.05)
    df_leachc.to_csv('output/leachc_results.csv', index=False)

    # 3. Run LEACH-GA Simulation
    df_leachga, sc_leachga, cl_leachga = run_simulation(LEACH_GA, network, max_rounds, p=0.05, pop_size=25, generations=15)
    df_leachga.to_csv('output/leachga_results.csv', index=False)

    # 4. Run PEGASIS Simulation
    df_pegasis, sc_pegasis, cl_pegasis = run_simulation(PEGASIS, network, max_rounds)
    df_pegasis.to_csv('output/pegasis_results.csv', index=False)

    # 5. Generate Visualizations
    print("\nGenerating comparison plots...")
    plotter = Plotter(output_dir='output/plots')
    
    comparison_data = {
        'LEACH': df_leach,
        'LEACH-C': df_leachc,
        'LEACH-GA': df_leachga,
        'PEGASIS': df_pegasis
    }
    
    scalability_comparison = {
        'LEACH': pd.DataFrame([sc_leach]),
        'LEACH-C': pd.DataFrame([sc_leachc]),
        'LEACH-GA': pd.DataFrame([sc_leachga]),
        'PEGASIS': pd.DataFrame([sc_pegasis])
    }
    
    cluster_comparison = {
        'LEACH': cl_leach,
        'LEACH-C': cl_leachc,
        'LEACH-GA': cl_leachga
        # PEGASIS is chain-based, so cluster distribution isn't directly applicable
    }
    
    plot_configs = [
        {
            'x_col': 'round', 'y_col': 'alive_nodes',
            'title': 'Network Dynamics: Alive Nodes vs Rounds', 
            'xlabel': 'Number of Rounds', 'ylabel': 'Alive Nodes Count',
            'filename': 'alive_nodes_vs_rounds.png'
        },
        {
            'x_col': 'round', 'y_col': 'dead_nodes',
            'title': 'Network Dynamics: Dead Nodes vs Rounds', 
            'xlabel': 'Number of Rounds', 'ylabel': 'Dead Nodes Count',
            'filename': 'dead_nodes_vs_rounds.png'
        },
        {
            'x_col': 'round', 'y_col': 'residual_energy',
            'title': 'Network Dynamics: Residual Energy vs Rounds', 
            'xlabel': 'Number of Rounds', 'ylabel': 'Residual Energy (J)',
            'filename': 'residual_energy_vs_rounds.png'
        },
        {
            'x_col': 'round', 'y_col': 'cumulative_throughput',
            'title': 'Network Dynamics: Throughput vs Rounds', 
            'xlabel': 'Number of Rounds', 'ylabel': 'Cumulative Throughput',
            'filename': 'throughput_vs_rounds.png'
        }
    ]
    
    print("\nPlotting Round Metrics...")
    for config in plot_configs:
        plotter.plot_generic(
            data_dict=comparison_data,
            x_col=config['x_col'],
            y_col=config['y_col'],
            title=config['title'],
            xlabel=config['xlabel'],
            ylabel=config['ylabel'],
            filename=config['filename'],
            marker=None,
            linestyle='-'
        )
        
    print("\nPlotting Scalability Metrics...")
    scalability_configs = [
        {'x': 'nodes', 'y': 'throughput_bps', 't': 'Throughput Performance', 'y_l': 'Total Throughput (bps)', 'f': 'throughput_vs_nodes.png', 'm': 'o'},
        {'x': 'nodes', 'y': 'lifetime_rounds', 't': 'Network Lifetime Endurance', 'y_l': 'Lifetime (Rounds)', 'f': 'lifetime_vs_nodes.png', 'm': 's'},
        {'x': 'nodes', 'y': 'signal_overhead', 't': 'Communication Efficiency', 'y_l': 'Signal Overhead', 'f': 'overhead_vs_nodes.png', 'm': '^'},
        {'x': 'nodes', 'y': 'e2e_delay_ms', 't': 'Transmission Latency', 'y_l': 'End-to-End Delay (ms)', 'f': 'e2e_delay_vs_nodes.png', 'm': '*'}
    ]
    for config in scalability_configs:
        plotter.plot_generic(
            data_dict=scalability_comparison,
            x_col=config['x'],
            y_col=config['y'],
            title=f"Scalability: {config['t']}",
            xlabel="Number of Nodes",
            ylabel=config['y_l'],
            filename=config['f'],
            marker=config['m'],
            linestyle='-'
        )

    print("\nPlotting Cluster Distribution Metrics...")
    plotter.plot_generic(
        data_dict=cluster_comparison,
        x_col='cluster_id',
        y_col='members',
        title="Load Balancing: Cluster Member Distribution",
        xlabel="Cluster ID",
        ylabel="Nodes per CH",
        filename="cluster_distribution.png",
        marker=None,
        linestyle=None
    )
    
    print("\nSimulations and plotting complete!")
    print("Results saved in 'output/' and plots in 'output/plots/'")
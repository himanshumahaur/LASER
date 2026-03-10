import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class Plotter:
    """
    Premium WSN Visualization Engine.
    Handles generic plotting based on input configuration.
    """
    
    # --- Configuration ---
    COLORS = {
        'Proposed (FASER)': '#8B0000', # Dark Red (Premium)
        'LEACH': '#0d6efd',         # Primary Blue
        'LEACH-GA': '#20c997',      # Teal
        'LEACH-C': '#fd7e14',        # Orange
        'PEGASIS': '#dc3545'        # Danger Red
    }
    
    STYLE_CONFIG = {
        'font.family': 'sans-serif',
        'font.sans-serif': ['Inter', 'Roboto', 'Arial'],
        'axes.facecolor': '#f8f9fa',
        'axes.grid': True,
        'grid.alpha': 0.3,
        'legend.frameon': True,
        'legend.facecolor': 'white',
        'legend.edgecolor': '#dee2e6',
        'figure.autolayout': True,
        'savefig.dpi': 300
    }

    def __init__(self, output_dir='plots/outputs'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.style.use('ggplot')
        plt.rcParams.update(self.STYLE_CONFIG)

    def _setup_plot(self, title, xlabel, ylabel, figsize=(10, 6)):
        fig, ax = plt.subplots(figsize=figsize)
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontweight='600')
        ax.set_ylabel(ylabel, fontweight='600')
        return fig, ax

    def _finalize_plot(self, filename):
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, bbox_inches='tight')
        plt.close()
        print(f"Viz saved: {path}")

    # --- Plotting Methods ---

    def plot_generic(self, data_dict, x_col, y_col, title, xlabel, ylabel, filename, marker=None, linestyle=None):
        """
        Plots metrics generically based on provided column names and labels.
        
        Args:
            data_dict (dict): Dictionary mapping protocol names to their DataFrames.
            x_col (str): Column name for x-axis.
            y_col (str): Column name for y-axis.
            title (str): Title of the plot.
            xlabel (str): Label for the x-axis.
            ylabel (str): Label for the y-axis.
            filename (str): Name of the output file.
            marker (str, optional): Marker style for the plot.
            linestyle (str, optional): Line style for the plot.
        """
        fig, ax = self._setup_plot(title, xlabel, ylabel)
        
        min_y = float('inf')
        
        for name, df in data_dict.items():
            if x_col not in df.columns or y_col not in df.columns:
                print(f"Warning: Columns '{x_col}' or '{y_col}' not found in data for {name}. Skipping.")
                continue
                
            color = self.COLORS.get(name)
            if not color:
                color = plt.cm.tab10(np.random.randint(0, 10))
            
            # Protocol specific styles or overrides
            current_marker = marker if marker is not None else ('*' if 'Proposed' in name else 'o')
            current_ls = linestyle if linestyle is not None else ('-' if 'Proposed' in name else '--')
            
            # Larger size for star marker
            msize = 10 if current_marker == '*' else 8
            if current_marker == '': msize = 0 # No marker
            
            ax.plot(df[x_col], df[y_col], label=name, color=color, 
                    marker=current_marker, linewidth=2.5, markersize=msize, 
                    linestyle=current_ls, alpha=0.9)
            
            current_min = df[y_col].min()
            if current_min < min_y:
                min_y = current_min
        
        if min_y != float('inf') and min_y >= 0:
            ax.set_ylim(bottom=0)
            
        ax.legend()
        self._finalize_plot(filename)

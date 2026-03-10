import pandas as pd
import os

class SensorDataReader:
    """
    Simplified and optimized reader for WSN data (Intel Lab Dataset).
    Efficiently loads and provides access to node locations and sensor readings.
    """
    def __init__(self, config):
        paths = config.get('path', {}).get('data', {})
        self.loc_path = paths.get('moteLocation')
        self.read_path = paths.get('moteReading')

        self.mote_locs = {}
        if self.loc_path and os.path.exists(self.loc_path):
            with open(self.loc_path, 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 3:
                        self.mote_locs[int(parts[0])] = (float(parts[1]), float(parts[2]))

        # Load Sensor Readings (Pandas for efficiency)
        self.all_readings = {} # Fast lookup: mote_id -> {epoch -> reading_dict}
        if self.read_path and os.path.exists(self.read_path):
            names = ['date', 'time', 'epoch', 'moteid', 'temp', 'humidity', 'light', 'voltage']
            try:
                df = pd.read_csv(self.read_path, sep=r'\s+', names=names, engine='python')
                df = df.drop_duplicates(subset=['moteid', 'epoch'], keep='first')
                
                # Group by moteid and store epochs in a dict for each node
                for mote_id, group in df.groupby('moteid'):
                    self.all_readings[mote_id] = group.set_index('epoch').to_dict('index')
            except Exception as e:
                print(f"Error loading sensor readings: {e}")

    def get_node_data(self, mote_id):
        """Returns all readings for a specific mote as an epoch-indexed dict."""
        return self.all_readings.get(mote_id, {})

    def get_mote_locations(self):
        """Returns the dictionary of all mote locations."""
        return self.mote_locs

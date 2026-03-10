import math

class EnergyModel:
    """
    Computes energy depletion for transmitting, receiving, and data processing (fusion) 
    according to the First Order Radio Model.
    """
    def __init__(self):
        # E_elec: Energy dissipation to run the transmitter or receiver circuitry
        self.E_elec = 50e-9  # 50 nJ/bit
        
        # epsilon_fs: Free space amplifier parameter
        self.epsilon_fs = 10e-12  # 10 pJ/bit/m^2
        
        # epsilon_mp: Multi-path attenuation amplifier parameter 
        # Typical value: 0.0013 pJ/bit/m^4 = 0.0013e-12 J/bit/m^4
        self.epsilon_mp = 0.0013e-12 
        
        # E_DA: Data Aggregation energy
        self.E_da = 5e-9  # 5 nJ/bit/signal
        
        # E_sleep: Energy for sleep mode (Idle energy)
        self.E_sleep = 0.5e-9 # 0.5 nJ per bit/round equivalent
        
        # Threshold distance d0 = sqrt(epsilon_fs / epsilon_mp)
        self.d_0 = math.sqrt(self.epsilon_fs / self.epsilon_mp)

    def tx_energy(self, k_bits, d):
        """Computes the energy required to transmit a k-bit message over distance d."""
        if d < self.d_0:
            # Free space model
            return (self.E_elec * k_bits) + (self.epsilon_fs * k_bits * (d ** 2))
        else:
            # Multipath model
            return (self.E_elec * k_bits) + (self.epsilon_mp * k_bits * (d ** 4))

    def rx_energy(self, k_bits):
        """Computes the energy required to receive a k-bit message."""
        return self.E_elec * k_bits

    def fusion_energy(self, k_bits, num_signals):
        """Computes the energy required to aggregate/fuse data."""
        return self.E_da * k_bits * num_signals

    def sleep_energy(self, k_bits):
        """Minimal energy required for a node in sleep mode."""
        return self.E_sleep * k_bits

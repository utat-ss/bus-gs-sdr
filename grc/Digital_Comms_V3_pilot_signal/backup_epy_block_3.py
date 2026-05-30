import numpy as np
from gnuradio import gr
import csv
import os
import time
from datetime import datetime

CSV_FILE = "V3_noise_vs_ber.csv"
LOG_INTERVAL = 0.8  # seconds between each periodic snapshot

class blk(gr.sync_block):
    """
    Records BER vs noise parameters to a CSV file periodically.
    Every LOG_INTERVAL seconds, snapshots the current parameters and BER.

    Inputs:
        in0: float32 BER estimate (from BER Calculator block)

    Parameters:
        noise_voltage:       TX noise voltage
        noise_freq_offset:   frequency offset applied to noise
        noise_timing_offset: timing offset applied to noise
    """

    def __init__(self, noise_voltage=0.0, noise_freq_offset=0.0, noise_timing_offset=0.0):
        gr.sync_block.__init__(
            self,
            name="BER vs Noise Logger",
            in_sig=[np.float32],
            out_sig=None,
        )

        self.noise_voltage       = noise_voltage
        self.noise_freq_offset   = noise_freq_offset
        self.noise_timing_offset = noise_timing_offset

        self.last_log_time = time.time()

        self._init_csv()

    def _init_csv(self):
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "timestamp",
                    "noise_voltage",
                    "noise_freq_offset",
                    "noise_timing_offset",
                    "ber",
                ])

    def _record(self, ber):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                self.noise_voltage,
                self.noise_freq_offset,
                self.noise_timing_offset,
                f"{ber:.8f}",
            ])
        print(f"[BER Logger] Recorded: voltage={self.noise_voltage} "
              f"freq_offset={self.noise_freq_offset} "
              f"timing_offset={self.noise_timing_offset} "
              f"BER={ber:.8f}")

    def work(self, input_items, output_items):
        ber_in = input_items[0]
        n = len(ber_in)

        now = time.time()
        if now - self.last_log_time >= LOG_INTERVAL:
            current_ber = float(np.mean(ber_in))
            self._record(current_ber)
            self.last_log_time = now

        return n

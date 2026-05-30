import numpy as np
from gnuradio import gr

class blk(gr.sync_block):
    def __init__(self, buffer_size=20000, max_offset=500, realign_interval=50000, periodic_realign=True):
        gr.sync_block.__init__(
            self,
            name='BER Calculator',
            in_sig=[np.uint8, np.uint8],
            out_sig=[np.float32]
        )
        self.buffer_size = buffer_size
        self.max_offset = max_offset
        self.realign_interval = realign_interval
        self.periodic_realign = periodic_realign
        self.tx_buffer = np.array([], dtype=np.uint8)
        self.rx_buffer = np.array([], dtype=np.uint8)
        self.synced = False
        self.offset = 0
        self.total_bits = 0
        self.total_errors = 0
        self.print_counter = 0
        self.realign_counter = 0
        self.last_ber = 0.0

    def find_offset(self):
        correlation = np.correlate(
            self.rx_buffer.astype(float),
            self.tx_buffer.astype(float),
            mode='full'
        )
        center = len(self.tx_buffer) - 1
        search = correlation[center - self.max_offset:center + self.max_offset]
        return np.argmax(search) - self.max_offset

    def align_buffers(self, offset):
        if offset >= 0:
            self.rx_buffer = self.rx_buffer[offset:]
        else:
            self.tx_buffer = self.tx_buffer[-offset:]
        print(f"[BER Block] Aligned. Offset: {offset}")

    def work(self, input_items, output_items):
        tx_in = input_items[0]
        rx_in = input_items[1]
        n = len(tx_in)

        self.tx_buffer = np.append(self.tx_buffer, tx_in)
        self.rx_buffer = np.append(self.rx_buffer, rx_in)

        if not self.synced:
            if len(self.tx_buffer) >= self.buffer_size:
                offset = self.find_offset()
                self.align_buffers(offset)
                self.synced = True
                print(f"[BER Block] Initial lock. Offset: {offset}")

        else:
            min_len = min(len(self.tx_buffer), len(self.rx_buffer))
            if min_len > 0:
                errors = np.sum(self.tx_buffer[:min_len] != self.rx_buffer[:min_len])
                self.total_errors += errors
                self.total_bits += min_len
                self.realign_counter += min_len

                self.tx_buffer = self.tx_buffer[min_len:]
                self.rx_buffer = self.rx_buffer[min_len:]

                self.print_counter += min_len
                if self.print_counter >= 1000:
                    self.last_ber = self.total_errors / self.total_bits
                    print(f"[BER Block] BER: {self.last_ber:.6f}")
                    self.print_counter = 0
                    self.total_bits = 0
                    self.total_errors = 0

                # Periodically re-align only if enabled
                if self.periodic_realign and self.realign_counter >= self.realign_interval:
                    self.realign_counter = 0
                    self.synced = False
                    self.tx_buffer = np.array([], dtype=np.uint8)
                    self.rx_buffer = np.array([], dtype=np.uint8)
                    print(f"[BER Block] Re-aligning...")

        output_items[0][:n] = self.last_ber
        return n
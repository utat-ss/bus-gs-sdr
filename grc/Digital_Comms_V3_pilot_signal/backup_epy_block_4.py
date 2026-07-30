import numpy as np
from gnuradio import gr

PILOT_LEN = 256

def pack_bits_with_offset(bits, bit_offset, bitorder):
    trimmed = bits[bit_offset:]
    n_bytes = len(trimmed) // 8
    if n_bytes == 0:
        return np.array([], dtype=np.uint8)
    usable = trimmed[:n_bytes * 8]
    return np.packbits(usable, bitorder=bitorder)

def is_increasing_mod256(packed, min_run=16):
    if len(packed) < 2:
        return 0.0
    expected_next = ((packed[:-1].astype(np.uint16) + 1) % 256).astype(np.uint8)
    good = np.sum(packed[1:] == expected_next)
    return good / (len(packed) - 1)

def find_best_alignment(bits, min_run=16):
    best = None
    best_score = 0.0
    for bitorder in ['big', 'little']:
        for bit_offset in range(8):
            packed = pack_bits_with_offset(bits, bit_offset, bitorder)
            if len(packed) < min_run:
                continue
            score = is_increasing_mod256(packed)
            if score > best_score:
                best_score = score
                byte_phase = int(packed[0])
                best = (bit_offset, bitorder, byte_phase, score)
    return best


class blk(gr.sync_block):
    def __init__(self, buffer_size=20000, realign_interval=50000, periodic_realign=True, score_threshold=0.8, stats_reset_interval=1000):
        gr.sync_block.__init__(
            self,
            name='BER Calculator 1',
            in_sig=[np.uint8],
            out_sig=[np.float32, np.float32]  # [BER, byte error rate]
        )
        self.buffer_size = buffer_size
        self.realign_interval = realign_interval
        self.periodic_realign = periodic_realign
        self.score_threshold = score_threshold
        self.stats_reset_interval = stats_reset_interval

        self.bit_buffer = np.array([], dtype=np.uint8)

        self.synced = False
        self.bit_offset = 0
        self.bitorder = 'big'
        self.byte_phase = 0

        self.total_bits = 0
        self.total_bit_errors = 0
        self.total_bytes = 0
        self.total_byte_errors = 0

        self.print_counter = 0
        self.realign_counter = 0
        self.last_ber = 0.0
        self.last_byter = 0.0

    def try_align(self):
        result = find_best_alignment(self.bit_buffer)
        if result is None:
            print("[BER] Could not find alignment.")
            return False

        bit_offset, bitorder, byte_phase, score = result

        # Always apply the best-effort alignment regardless of score
        self.bit_offset = bit_offset
        self.bitorder = bitorder
        self.byte_phase = byte_phase
        self.bit_buffer = self.bit_buffer[bit_offset:]

        if score >= self.score_threshold:
            print(f"[BER] Locked. bit_offset={bit_offset} bitorder={bitorder} byte_phase={byte_phase} score={score:.4f}")
            return True  # full lock — stop retrying alignment
        else:
            print(f"[BER] Best-effort alignment. bit_offset={bit_offset} bitorder={bitorder} byte_phase={byte_phase} score={score:.4f} (below threshold, will keep retrying)")
            return False  # not locked — keep retrying, but still compute BER

    def _compute_ber(self):
        n_bytes = len(self.bit_buffer) // 8
        if n_bytes == 0:
            return

        usable = self.bit_buffer[:n_bytes * 8]
        packed = np.packbits(usable, bitorder=self.bitorder)
        self.bit_buffer = self.bit_buffer[n_bytes * 8:]

        expected = ((self.byte_phase + np.arange(n_bytes)) % PILOT_LEN).astype(np.uint8)
        self.byte_phase = int((self.byte_phase + n_bytes) % PILOT_LEN)

        byte_errors = int(np.sum(packed != expected))
        self.total_bytes += n_bytes
        self.total_byte_errors += byte_errors

        xor = np.bitwise_xor(packed, expected)
        bit_errors = int(np.sum(np.unpackbits(xor)))
        self.total_bits += n_bytes * 8
        self.total_bit_errors += bit_errors

        self.realign_counter += n_bytes
        self.print_counter += n_bytes

        if self.print_counter >= self.stats_reset_interval:
            self.last_ber = self.total_bit_errors / self.total_bits if self.total_bits else 0.0
            self.last_byter = self.total_byte_errors / self.total_bytes if self.total_bytes else 0.0
            locked_str = "LOCKED" if self.synced else "best-effort"
            print(f"[BER] [{locked_str}] BER={self.last_ber:.6f}  ByteER={self.last_byter:.6f}  bits={self.total_bits}  bytes={self.total_bytes}")
            self.print_counter = 0
            self.total_bits = 0
            self.total_bit_errors = 0
            self.total_bytes = 0
            self.total_byte_errors = 0

    def work(self, input_items, output_items):
        bits_in = input_items[0]
        n = len(bits_in)

        self.bit_buffer = np.append(self.bit_buffer, bits_in)

        if not self.synced:
            if len(self.bit_buffer) >= self.buffer_size:
                self.synced = self.try_align()
                if not self.synced:
                    # Not locked but still compute BER with best-effort alignment,
                    # then discard half the buffer and re-search next time
                    self._compute_ber()
                    self.bit_buffer = self.bit_buffer[self.buffer_size // 2:]
        else:
            self._compute_ber()

            if self.periodic_realign and self.realign_counter >= self.realign_interval:
                self.realign_counter = 0
                self.synced = False
                self.bit_buffer = np.array([], dtype=np.uint8)
                print("[BER] Re-aligning...")

        output_items[0][:n] = self.last_ber
        output_items[1][:n] = self.last_byter
        return n

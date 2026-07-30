# import numpy as np
# from gnuradio import gr
#
# PILOT_LEN = 256
#
# def pack_bits_with_offset(bits, bit_offset, bitorder):
#     trimmed = bits[bit_offset:]
#     n_bytes = len(trimmed) // 8
#     if n_bytes == 0:
#         return np.array([], dtype=np.uint8)
#     usable = trimmed[:n_bytes * 8]
#     return np.packbits(usable, bitorder=bitorder)
#
# def is_increasing_mod256(packed, min_run=16):
#     """
#     Check if packed bytes look like the repeating 0..255 ramp.
#     Returns fraction of consecutive pairs that are +1 mod 256.
#     """
#     if len(packed) < 2:
#         return 0.0
#     expected_next = ((packed[:-1].astype(np.uint16) + 1) % 256).astype(np.uint8)
#     good = np.sum(packed[1:] == expected_next)
#     return good / (len(packed) - 1)
#
# def find_best_alignment(bits, min_run=16):
#     """
#     Try all 8 bit offsets for a fixed (harcoded!) bit order.
#     Returns (best_bit_offset, best_bitorder, best_byte_phase) or None.
#     """
#     best = None
#     best_score = 0.0
#
#     bitorder = "big" # hardcoded
#
#     for bit_offset in range(8):
#         packed = pack_bits_with_offset(bits, bit_offset, bitorder)
#         if len(packed) < min_run:
#             continue
#         score = is_increasing_mod256(packed)
#         if score > best_score:
#             # find byte phase: which value does the sequence start at?
#             best_score = score
#             # estimate byte phase from first byte
#             byte_phase = int(packed[0])
#             best = (bit_offset, bitorder, byte_phase, score)
#
#     return best  # None if nothing found
#
#
# class blk(gr.sync_block):
#     def __init__(self, buffer_size=20000, realign_interval=50000, periodic_realign=True, score_threshold=0.2, stats_reset_interval=1000):
#         gr.sync_block.__init__(
#             self,
#             name='BER Calculator',
#             in_sig=[np.uint8],       # unpacked bit stream (0s and 1s)
#             out_sig=[np.float32, np.float32]  # [BER, byte error rate]
#         )
#         self.buffer_size = buffer_size
#         self.realign_interval = realign_interval
#         self.periodic_realign = periodic_realign
#         self.score_threshold = score_threshold
#
#         self.bit_buffer = np.array([], dtype=np.uint8)
#
#         self.synced = False
#         self.bit_offset = 0
#         self.bitorder = 'big'
#         self.byte_phase = 0         # which value in 0..255 we expect next
#
#         self.total_bits = 0
#         self.total_bit_errors = 0
#         self.total_bytes = 0
#         self.total_byte_errors = 0
#
#         self.print_counter = 0
#         self.realign_counter = 0
#         self.last_ber = 0.0
#         self.last_byter = 0.0
#
#         self.stats_reset_interval = stats_reset_interval
#
#     def try_align(self):
#         '''
#         calls find_best_alignment() to find the best alignment out of the 16 orders, and
#         returns True if the score is larger than score_threshold
#         '''
#
#
#         result = find_best_alignment(self.bit_buffer)
#         if result is None:
#             print("[BER] Could not find alignment.")
#             # return False
#         bit_offset, bitorder, byte_phase, score = result
#         self.bit_offset = bit_offset
#         self.bitorder = bitorder
#         self.byte_phase = byte_phase
#         # consume the bits used for alignment
#         self.bit_buffer = self.bit_buffer[bit_offset:]
#         print(f"[BER] bit_offset={bit_offset} byte_phase={byte_phase} score={score:.4f}")
#
#         if score > self.score_threshold:
#             return True
#         else:
#             print("Bad alignment score")
#             return False
#
#     def work(self, input_items, output_items):
#         bits_in = input_items[0]
#         n = len(bits_in)
#
#         self.bit_buffer = np.append(self.bit_buffer, bits_in)
#
#         if not self.synced:
#             if len(self.bit_buffer) >= self.buffer_size:
#                 self.synced = self.try_align()
#                 if not self.synced:
#                     # discard half the buffer and try again next time
#                     self.bit_buffer = self.bit_buffer[self.buffer_size // 2:]
#
#         else:
#             # pack available bits into bytes using locked alignment
#             n_bytes = len(self.bit_buffer) // 8
#             if n_bytes > 0:
#                 usable = self.bit_buffer[:n_bytes * 8]
#                 packed = np.packbits(usable, bitorder=self.bitorder)
#                 self.bit_buffer = self.bit_buffer[n_bytes * 8:]
#
#                 # build expected ramp
#                 expected = ((self.byte_phase + np.arange(n_bytes)) % PILOT_LEN).astype(np.uint8)
#                 self.byte_phase = int((self.byte_phase + n_bytes) % PILOT_LEN)
#
#                 # byte errors
#                 byte_errors = int(np.sum(packed != expected))
#                 self.total_bytes += n_bytes
#                 self.total_byte_errors += byte_errors
#
#                 # bit errors
#                 xor = np.bitwise_xor(packed, expected)
#                 bit_errors = int(np.sum(np.unpackbits(xor)))
#                 self.total_bits += n_bytes * 8
#                 self.total_bit_errors += bit_errors
#
#                 self.realign_counter += n_bytes
#                 self.print_counter += n_bytes
#
#                 if self.print_counter >= self.stats_reset_interval:
#                     self.last_ber = self.total_bit_errors / self.total_bits if self.total_bits else 0.0
#                     self.last_byter = self.total_byte_errors / self.total_bytes if self.total_bytes else 0.0
#                     print(f"[BER] BER={self.last_ber:.6f}  ByteER={self.last_byter:.6f}  bits={self.total_bits}  bytes={self.total_bytes}")
#                     self.print_counter = 0
#                     self.total_bits = 0
#                     self.total_bit_errors = 0
#                     self.total_bytes = 0
#                     self.total_byte_errors = 0
#
#
#                 if self.periodic_realign and self.realign_counter >= self.realign_interval:
#                     self.realign_counter = 0
#                     self.synced = False
#                     self.bit_buffer = np.array([], dtype=np.uint8)
#                     print("[BER] Re-aligning...")
#
#         output_items[0][:n] = self.last_ber
#         output_items[1][:n] = self.last_byter
#         return n
"""
GNU Radio BER calculator block for a known pilot stream.

The input is an unpacked bit stream (0/1 values). The block tries to lock
onto a repeating byte ramp, counts BER and byte error rate continuously, and
keeps running even when lock is lost.

Pilot pattern:
0, 1, 2, ..., 255 repeated, with both 255 and 256-period interpretations
checked during alignment.
"""

import numpy as np
from gnuradio import gr

PILOT_LEN_CANDIDATES = (255, 256)


def pack_bits_with_offset(bits, bit_offset, bitorder):
    trimmed = bits[bit_offset:]
    n_bytes = len(trimmed) // 8
    if n_bytes == 0:
        return np.array([], dtype=np.uint8)
    usable = trimmed[:n_bytes * 8]
    return np.packbits(usable, bitorder=bitorder)


def best_exact_ramp_score(packed, pilot_len):
    """Return the best phase and exact-match fraction for a given pilot length."""
    if len(packed) == 0:
        return 0, 0.0

    i_mod = (np.arange(len(packed), dtype=np.uint32) % pilot_len).astype(np.uint16)
    packed_u16 = packed.astype(np.uint16)
    phase_vec = (packed_u16 - i_mod) % pilot_len
    counts = np.bincount(phase_vec.astype(np.int64), minlength=pilot_len)
    phase = int(np.argmax(counts))
    score = float(counts[phase]) / float(len(packed))
    return phase, score


def find_best_alignment(bits, min_run=16):
    """
    Try all 8 bit offsets x 2 bit orders x candidate pilot lengths.
    Returns (best_bit_offset, best_bitorder, best_byte_phase, best_pilot_len, score) or None.
    """
    best = None
    best_score = 0.0

    for bitorder in ['big', 'little']:
        for bit_offset in range(8):
            packed = pack_bits_with_offset(bits, bit_offset, bitorder)
            if len(packed) < min_run:
                continue
            for pilot_len in PILOT_LEN_CANDIDATES:
                byte_phase, score = best_exact_ramp_score(packed, pilot_len)
                if score > best_score:
                    best_score = score
                    best = (bit_offset, bitorder, byte_phase, pilot_len, score)

    return best


class blk(gr.sync_block):
    def __init__(self, buffer_size=20000, realign_interval=50000, periodic_realign=True, score_threshold=0.8, stats_reset_interval=1000):
        gr.sync_block.__init__(
            self,
            name='BER Calculator',
            in_sig=[np.uint8],
            out_sig=[np.float32, np.float32],
        )
        self.buffer_size = buffer_size
        self.realign_interval = realign_interval
        self.periodic_realign = periodic_realign
        self.score_threshold = score_threshold

        self.bit_buffer = np.array([], dtype=np.uint8)
        self.count_buffer = np.array([], dtype=np.uint8)

        self.synced = False
        self.bit_offset = 0
        self.bitorder = 'big'
        self.byte_phase = 0
        self.pilot_len = 256

        self.total_bits = 0
        self.total_bit_errors = 0
        self.total_bytes = 0
        self.total_byte_errors = 0

        self.print_counter = 0
        self.realign_counter = 0
        self.last_ber = 0.0
        self.last_byter = 0.0
        self.stats_reset_interval = stats_reset_interval
        self.work_calls = 0

        print(
            f'[BER] init buffer_size={buffer_size} realign_interval={realign_interval} '
            f'periodic_realign={periodic_realign} score_threshold={score_threshold} '
            f'stats_reset_interval={stats_reset_interval}',
            flush=True,
        )

    def try_align(self):
        print(f'[BER] try_align buffer_len={len(self.bit_buffer)}', flush=True)
        result = find_best_alignment(self.bit_buffer)
        if result is None:
            print('[BER] Could not find alignment.', flush=True)
            return False

        bit_offset, bitorder, byte_phase, pilot_len, score = result
        if score < self.score_threshold:
            print(f'[BER] Best alignment score {score:.3f} below threshold {self.score_threshold}. Not locking.', flush=True)
            return False

        self.bit_offset = bit_offset
        self.bitorder = bitorder
        self.byte_phase = byte_phase
        self.pilot_len = pilot_len
        self.bit_buffer = self.bit_buffer[bit_offset:]
        print(
            f'[BER] Locked. bit_offset={bit_offset} bitorder={bitorder} '
            f'byte_phase={byte_phase} pilot_len={pilot_len} score={score:.4f}'
        , flush=True)
        return True

    def count_available_bytes(self):
        n_bytes = len(self.count_buffer) // 8
        if n_bytes == 0:
            return

        usable = self.count_buffer[:n_bytes * 8]
        packed = np.packbits(usable, bitorder=self.bitorder)
        self.count_buffer = self.count_buffer[n_bytes * 8:]

        expected = ((self.byte_phase + np.arange(n_bytes)) % self.pilot_len).astype(np.uint8)
        byte_errors = int(np.sum(packed != expected))
        xor = np.bitwise_xor(packed, expected)
        bit_errors = int(np.sum(np.unpackbits(xor)))

        self.total_bytes += n_bytes
        self.total_byte_errors += byte_errors
        self.total_bits += n_bytes * 8
        self.total_bit_errors += bit_errors

        if self.synced and byte_errors > 0:
            self.synced = False
            print('[BER] Lost lock, but BER counting continues.', flush=True)

        print(
            f'[BER] count_available_bytes n_bytes={n_bytes} byte_errors={byte_errors} '
            f'bit_errors={bit_errors} next_phase={self.byte_phase} synced={self.synced}',
            flush=True,
        )

        self.byte_phase = int((self.byte_phase + n_bytes) % self.pilot_len)
        self.realign_counter += n_bytes
        self.print_counter += n_bytes

    def work(self, input_items, output_items):
        bits_in = input_items[0]
        n = len(bits_in)
        self.work_calls += 1

        print(
            f'[BER] work call={self.work_calls} n={n} '
            f'bit_buffer={len(self.bit_buffer)} count_buffer={len(self.count_buffer)} synced={self.synced}',
            flush=True,
        )

        self.bit_buffer = np.append(self.bit_buffer, bits_in)
        self.count_buffer = np.append(self.count_buffer, bits_in)

        self.count_available_bytes()

        if not self.synced and len(self.bit_buffer) >= self.buffer_size:
            self.synced = self.try_align()
            if not self.synced:
                self.bit_buffer = self.bit_buffer[self.buffer_size // 2:]

        if self.print_counter >= self.stats_reset_interval:
            self.last_ber = self.total_bit_errors / self.total_bits if self.total_bits else 0.0
            self.last_byter = self.total_byte_errors / self.total_bytes if self.total_bytes else 0.0
            print(f'[BER] BER={self.last_ber:.6f}  ByteER={self.last_byter:.6f}  bits={self.total_bits}  bytes={self.total_bytes}', flush=True)
            self.print_counter = 0
            self.total_bits = 0
            self.total_bit_errors = 0
            self.total_bytes = 0
            self.total_byte_errors = 0

        if self.periodic_realign and self.realign_counter >= self.realign_interval:
            self.realign_counter = 0
            self.synced = False
            self.bit_buffer = np.array([], dtype=np.uint8)
            print('[BER] Re-aligning...', flush=True)

        if len(self.bit_buffer) > self.buffer_size * 2:
            self.bit_buffer = self.bit_buffer[-self.buffer_size:]

        if self.work_calls % 50 == 0:
            print(
                f'[BER] status work_calls={self.work_calls} bit_buffer={len(self.bit_buffer)} '
                f'count_buffer={len(self.count_buffer)} total_bits={self.total_bits} '
                f'total_bit_errors={self.total_bit_errors} synced={self.synced}',
                flush=True,
            )

        output_items[0][:n] = self.last_ber
        output_items[1][:n] = self.last_byter
        return n

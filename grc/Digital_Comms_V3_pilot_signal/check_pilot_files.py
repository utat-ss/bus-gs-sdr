"""
check_pilot_files.py

Checks:
1. TX file right after 0-255 pilot source
2. RX file right before Pilot BER Calculator

Assumes both are uint8 byte streams.
"""

import os
import numpy as np


TX_FILE = "pilot_tx.txt"   # change to your TX file sink name
RX_FILE = "pilot_rx.txt"   # change to your RX file sink name

SAMPLE_BYTES = 200_000
PILOT_LEN = 256


def load_sample(path, max_bytes=SAMPLE_BYTES):
    if not os.path.exists(path):
        print(f"ERROR: {path} does not exist")
        return None

    size = os.path.getsize(path)
    n = min(size, max_bytes)

    data = np.fromfile(path, dtype=np.uint8, count=n)

    print("=" * 70)
    print(f"File: {path}")
    print(f"Size: {size:,} bytes")
    print(f"Sampled: {len(data):,} bytes")

    if len(data) == 0:
        print("ERROR: file is empty")
        return None

    print("First 64 bytes:")
    print(data[:64])

    unique = np.unique(data)
    print(f"Unique values in sample: {len(unique)}")
    print(f"Min/max: {data.min()} / {data.max()}")

    return data


def expected_pilot(start, n):
    return ((start + np.arange(n)) % PILOT_LEN).astype(np.uint8)


def check_exact_0_to_255_pattern(data, name):
    """
    Finds best phase offset for repeated 0..255 pattern.
    Reports byte error rate and bit error rate against that pattern.
    """

    print()
    print(f"Pattern check for {name}:")

    best_offset = None
    best_byte_errors = None

    # Try all possible 0..255 pilot phases
    for offset in range(PILOT_LEN):
        ref = expected_pilot(offset, len(data))
        byte_errors = int(np.sum(data != ref))

        if best_byte_errors is None or byte_errors < best_byte_errors:
            best_byte_errors = byte_errors
            best_offset = offset

    ref = expected_pilot(best_offset, len(data))

    byte_errors = int(np.sum(data != ref))
    byte_error_rate = byte_errors / len(data)

    xor = np.bitwise_xor(data, ref)
    bit_errors = int(np.sum(np.unpackbits(xor)))
    total_bits = 8 * len(data)
    ber = bit_errors / total_bits

    print(f"Best pilot offset: {best_offset}")
    print(f"Byte errors: {byte_errors:,} / {len(data):,}")
    print(f"Byte error rate: {byte_error_rate:.6f} ({byte_error_rate * 100:.4f}%)")
    print(f"Bit errors: {bit_errors:,} / {total_bits:,}")
    print(f"BER vs 0-255 pilot: {ber:.6f} ({ber * 100:.4f}%)")

    if byte_errors == 0:
        print("PASS: exact repeated 0..255 pattern.")
    elif ber > 0.49:
        print("WARNING: BER near 0.5 — file does not look aligned with 0..255 pilot.")
    else:
        print("Partial match — probably some corruption, offset, or dropped/inserted bytes.")

    return best_offset, ber, byte_error_rate


def check_adjacent_differences(data, name):
    """
    For a perfect 0..255 ramp, each next byte should be previous + 1 mod 256.
    This detects whether the file is locally ramp-like even if global offset is unknown.
    """

    print()
    print(f"Continuity check for {name}:")

    if len(data) < 2:
        print("Not enough data.")
        return

    expected_next = ((data[:-1].astype(np.uint16) + 1) % 256).astype(np.uint8)
    good_steps = int(np.sum(data[1:] == expected_next))
    total_steps = len(data) - 1
    good_fraction = good_steps / total_steps

    print(f"Correct +1 mod 256 steps: {good_steps:,} / {total_steps:,}")
    print(f"Fraction correct: {good_fraction:.6f} ({good_fraction * 100:.4f}%)")

    if good_fraction > 0.999:
        print("PASS: locally looks like repeated 0..255.")
    elif good_fraction > 0.9:
        print("Mostly ramp-like, but with occasional slips/errors.")
    else:
        print("Not ramp-like.")


def compare_tx_rx(tx, rx):
    """
    Compare TX and RX samples after finding best byte offset.
    This is separate from comparing RX to ideal 0..255 pilot.
    """

    print()
    print("=" * 70)
    print("TX/RX comparison:")

    max_offset = 2000
    best_offset = None
    best_errors = None
    best_n = None

    for offset in range(-max_offset, max_offset + 1):
        if offset >= 0:
            # RX starts later than TX by offset bytes
            tx_cmp = tx[offset:]
            rx_cmp = rx
        else:
            # RX starts earlier than TX by -offset bytes
            tx_cmp = tx
            rx_cmp = rx[-offset:]

        n = min(len(tx_cmp), len(rx_cmp))
        if n <= 0:
            continue

        tx_cmp = tx_cmp[:n]
        rx_cmp = rx_cmp[:n]

        errors = int(np.sum(tx_cmp != rx_cmp))

        if best_errors is None or errors < best_errors:
            best_errors = errors
            best_offset = offset
            best_n = n

    if best_offset >= 0:
        print(f"Best offset: RX lags TX by {best_offset} bytes")
        tx_cmp = tx[best_offset:]
        rx_cmp = rx
    else:
        print(f"Best offset: RX leads TX by {-best_offset} bytes")
        tx_cmp = tx
        rx_cmp = rx[-best_offset:]

    n = min(len(tx_cmp), len(rx_cmp))
    tx_cmp = tx_cmp[:n]
    rx_cmp = rx_cmp[:n]

    byte_errors = int(np.sum(tx_cmp != rx_cmp))
    byte_error_rate = byte_errors / n

    xor = np.bitwise_xor(tx_cmp, rx_cmp)
    bit_errors = int(np.sum(np.unpackbits(xor)))
    ber = bit_errors / (8 * n)

    print(f"Compared: {n:,} bytes")
    print(f"Byte errors: {byte_errors:,} / {n:,}")
    print(f"Byte error rate: {byte_error_rate:.6f} ({byte_error_rate * 100:.4f}%)")
    print(f"Bit errors: {bit_errors:,} / {8 * n:,}")
    print(f"BER: {ber:.6f} ({ber * 100:.4f}%)")


def main():
    tx = load_sample(TX_FILE)
    rx = load_sample(RX_FILE)

    if tx is not None:
        check_exact_0_to_255_pattern(tx, "TX file")
        check_adjacent_differences(tx, "TX file")

    if rx is not None:
        check_exact_0_to_255_pattern(rx, "RX file")
        check_adjacent_differences(rx, "RX file")

    if tx is not None and rx is not None:
        compare_tx_rx(tx, rx)


if __name__ == "__main__":
    main()

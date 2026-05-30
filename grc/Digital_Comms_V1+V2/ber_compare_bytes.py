"""
ber_compare_bytes.py
====================
Offline BER calculation between two GNU Radio File Sink outputs.

Usage:
    python3 ber_compare_bytes.py ber_input.txt ber_output.txt

Both files should be raw binary uint8 byte streams.
This script:
  1. Loads both files as uint8 bytes
  2. Finds byte-level lag using cross-correlation
  3. Aligns the streams by byte lag
  4. Computes bit error rate by XOR + bit counting
"""

import numpy as np
import sys
import os


def load_bytes(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    data = np.fromfile(path, dtype=np.uint8)
    print(f"Loaded {len(data):,} bytes from {path}")
    return data


def find_lag(tx, rx, cal_size=100_000):
    """
    Cross-correlate a window of tx and rx to find the byte lag.

    Returns lag in bytes.

    Convention used here:
      lag > 0 means RX lags TX, so trim TX front.
      lag < 0 means RX leads TX, so trim RX front.
    """
    from scipy.signal import correlate, correlation_lags

    n = min(cal_size, len(tx), len(rx))

    # Convert bytes to zero-mean float for correlation
    tx_cal = tx[:n].astype(np.float32) - np.mean(tx[:n])
    rx_cal = rx[:n].astype(np.float32) - np.mean(rx[:n])

    print(f"Running cross-correlation on first {n:,} bytes...")
    corr = correlate(rx_cal, tx_cal, mode="full", method="fft")
    lags = correlation_lags(len(rx_cal), len(tx_cal), mode="full")

    lag = int(lags[np.argmax(corr)])

    print(
        f"Lag found: {lag} bytes "
        f"({'RX lags TX' if lag > 0 else 'RX leads TX' if lag < 0 else 'perfectly aligned'})"
    )

    return lag


def align(tx, rx, lag):
    """
    Align tx and rx by byte lag.

    lag > 0: RX lags TX, so remove first lag bytes from TX.
    lag < 0: RX leads TX, so remove first -lag bytes from RX.
    """
    if lag > 0:
        tx = tx[lag:]
    elif lag < 0:
        rx = rx[-lag:]

    n = min(len(tx), len(rx))
    return tx[:n], rx[:n]


def compute_ber_bytes(tx, rx):
    """
    Compute bit error rate for byte streams.

    Each byte contributes 8 bits.
    Errors are counted using XOR bit counts.
    """
    xor = np.bitwise_xor(tx, rx)

    # np.unpackbits gives all individual error bits
    bit_errors = int(np.sum(np.unpackbits(xor)))
    total_bits = len(xor) * 8

    ber = bit_errors / total_bits if total_bits > 0 else float("nan")
    return ber, bit_errors, total_bits


def compute_byte_error_rate(tx, rx):
    byte_errors = int(np.sum(tx != rx))
    total_bytes = len(tx)
    byte_er = byte_errors / total_bytes if total_bytes > 0 else float("nan")
    return byte_er, byte_errors, total_bytes


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 ber_compare_bytes.py <tx_file> <rx_file>")
        sys.exit(1)

    tx_path = sys.argv[1]
    rx_path = sys.argv[2]

    tx = load_bytes(tx_path)
    rx = load_bytes(rx_path)

    print()
    print("Sanity check:")
    print(f"  TX first 20 bytes: {tx[:20]}")
    print(f"  RX first 20 bytes: {rx[:20]}")
    print(f"  RX/TX size ratio:  {len(rx) / len(tx):.6f}" if len(tx) else "  TX is empty")

    lag = find_lag(tx, rx)
    tx_aligned, rx_aligned = align(tx, rx, lag)

    ber, bit_errors, total_bits = compute_ber_bytes(tx_aligned, rx_aligned)
    byte_er, byte_errors, total_bytes = compute_byte_error_rate(tx_aligned, rx_aligned)

    print()
    print("=" * 50)
    print(f"  Lag:              {lag} bytes")
    print(f"  Compared:         {total_bytes:,} bytes")
    print(f"  Byte errors:      {byte_errors:,} / {total_bytes:,}")
    print(f"  Byte error rate:  {byte_er:.6f}  ({byte_er * 100:.4f}%)")
    print(f"  Bit errors:       {bit_errors:,} / {total_bits:,} bits")
    print(f"  BER:              {ber:.6f}  ({ber * 100:.4f}%)")
    print("=" * 50)

    if ber > 0.49:
        print("WARNING: BER near 0.5 — alignment likely failed or streams are uncorrelated.")
    elif byte_er > 0.9 and ber < 0.1:
        print("NOTE: Many bytes differ, but BER is low. This can happen when only a few bits per byte are wrong.")


if __name__ == "__main__":
    main()

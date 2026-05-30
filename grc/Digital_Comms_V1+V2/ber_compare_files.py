"""
ber_compare.py
==============
Offline BER calculation between two GNU Radio File Sink outputs.

Usage:
    python3 ber_compare.py ber_input.txt ber_output.txt

Both files should be raw binary uint8 streams (unpacked bits, values 0 and 1),
as written by a GRC File Sink connected after an Unpack K Bits block.
"""

import numpy as np
import sys
import os


def load_bits(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    bits = np.fromfile(path, dtype=np.uint8)
    print(f"Loaded {len(bits):,} bits from {path}")
    return bits


def find_lag(tx, rx, cal_size=100_000):
    """
    Cross-correlate a window of tx and rx to find the lag.
    Uses FFT-based correlation for speed on large files.
    Returns lag in bits (positive = rx is ahead of tx).
    """
    from scipy.signal import correlate, correlation_lags

    # Cap to cal_size for speed — no need to correlate the whole file
    n = min(cal_size, len(tx), len(rx))
    tx_cal = (tx[:n].astype(np.float32)) - 0.5
    rx_cal = (rx[:n].astype(np.float32)) - 0.5

    print(f"Running cross-correlation on first {n:,} bits (this may take a moment)...")
    corr = correlate(rx_cal, tx_cal, mode='full', method='fft')
    lags = correlation_lags(len(rx_cal), len(tx_cal), mode='full')
    lag = int(lags[np.argmax(corr)])

    print(f"Lag found: {lag} bits ({'rx leads' if lag > 0 else 'tx leads' if lag < 0 else 'perfectly aligned'})")
    return lag


def align(tx, rx, lag):
    """Trim the leading stream to align tx and rx."""
    if lag > 0:
        # rx is ahead — trim rx front
        rx = rx[lag:]
    elif lag < 0:
        # tx is ahead — trim tx front
        tx = tx[-lag:]
    # Trim to same length
    n = min(len(tx), len(rx))
    return tx[:n], rx[:n]


def compute_ber(tx, rx):
    errors = int(np.sum(tx != rx))
    total = len(tx)
    ber = errors / total
    return ber, errors, total


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 ber_compare.py <tx_file> <rx_file>")
        sys.exit(1)

    tx_path = sys.argv[1]
    rx_path = sys.argv[2]

    tx = load_bits(tx_path)
    rx = load_bits(rx_path)

    # Sanity check — values should all be 0 or 1
    for name, arr in [("TX", tx), ("RX", rx)]:
        unique = np.unique(arr)
        if not np.all((unique == 0) | (unique == 1)):
            print(f"WARNING: {name} file contains values other than 0/1: {unique}")
            print("         Are you sure this is an unpacked bit stream?")

    lag = find_lag(tx, rx)
    tx_aligned, rx_aligned = align(tx, rx, lag)

    ber, errors, total = compute_ber(tx_aligned, rx_aligned)

    print()
    print("=" * 40)
    print(f"  Lag:    {lag} bits")
    print(f"  Errors: {errors:,} / {total:,} bits")
    print(f"  BER:    {ber:.6f}  ({ber*100:.4f}%)")
    print("=" * 40)

    # Warn if BER looks suspicious
    if ber > 0.49:
        print("WARNING: BER near 0.5 — alignment likely failed or streams are uncorrelated.")
    elif abs(ber - 0.125) < 0.01:
        print("WARNING: BER near 12.5% (1/8) — possible 1-bit byte boundary offset upstream.")


if __name__ == "__main__":
    main()

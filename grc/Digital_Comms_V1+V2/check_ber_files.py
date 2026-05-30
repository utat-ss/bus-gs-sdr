import os
import numpy as np

FILES = ["ber_src", "ber_rx"]
SAMPLE_SIZE = 1_000_000  # bytes sampled from the start of each file

def analyze_file(path):
    print("=" * 60)
    print(f"File: {path}")

    if not os.path.exists(path):
        print("ERROR: file does not exist")
        return

    size = os.path.getsize(path)
    print(f"Size: {size:,} bytes")

    n = min(SAMPLE_SIZE, size)
    data = np.fromfile(path, dtype=np.uint8, count=n)

    if len(data) == 0:
        print("ERROR: file is empty")
        return

    num_zeros = np.count_nonzero(data == 0)
    num_ones = np.count_nonzero(data == 1)
    num_binary = num_zeros + num_ones
    num_other = len(data) - num_binary

    print(f"Sampled: {len(data):,} bytes")
    print(f"0 count: {num_zeros:,} ({num_zeros / len(data) * 100:.2f}%)")
    print(f"1 count: {num_ones:,} ({num_ones / len(data) * 100:.2f}%)")
    print(f"Other values: {num_other:,} ({num_other / len(data) * 100:.2f}%)")

    if num_binary > 0:
        zero_fraction_within_binary = num_zeros / num_binary
        one_fraction_within_binary = num_ones / num_binary
        print(f"Within 0/1 values:")
        print(f"  0 fraction: {zero_fraction_within_binary * 100:.2f}%")
        print(f"  1 fraction: {one_fraction_within_binary * 100:.2f}%")

    unique_preview = np.unique(data[:10000])
    print(f"Unique values in first 10,000 bytes: {unique_preview[:50]}")
    if len(unique_preview) > 50:
        print(f"... plus {len(unique_preview) - 50} more unique values")

    mostly_binary = num_other / len(data) < 0.001
    roughly_balanced = abs(num_zeros - num_ones) / max(num_binary, 1) < 0.1

    print()
    print(f"Mostly 0/1? {'YES' if mostly_binary else 'NO'}")
    print(f"Roughly balanced 0s and 1s? {'YES' if roughly_balanced else 'NO'}")


def main():
    print("BER file sanity check")
    print(f"Sample size per file: {SAMPLE_SIZE:,} bytes")
    print()

    sizes = {}

    for path in FILES:
        if os.path.exists(path):
            sizes[path] = os.path.getsize(path)
        analyze_file(path)

    print("=" * 60)
    print("Size comparison:")

    if all(path in sizes for path in FILES):
        input_size = sizes["ber_src"]
        output_size = sizes["ber_rx"]

        print(f"ber_input.txt:  {input_size:,} bytes")
        print(f"ber_output.txt: {output_size:,} bytes")

        if input_size > 0:
            ratio = output_size / input_size
            print(f"output/input ratio: {ratio:.6f}")

            if abs(ratio - 1) < 0.05:
                print("Sizes are roughly equal.")
            elif abs(ratio - 2) < 0.1:
                print("Output is roughly 2x input.")
            elif abs(ratio - 4) < 0.2:
                print("Output is roughly 4x input — suspicious for bit/symbol packing mismatch.")
            elif abs(ratio - 8) < 0.4:
                print("Output is roughly 8x input — suspicious for byte-to-bit unpacking mismatch.")
            else:
                print("Sizes are not close to a common simple ratio.")

    for path in FILES:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed {path}")
if __name__ == "__main__":
    main()

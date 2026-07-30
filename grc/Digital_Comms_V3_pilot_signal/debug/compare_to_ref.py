import numpy as np

def byte_to_bits_msb(n):
    return [(n >> i) & 1 for i in range(7, -1, -1)]

# build reference: unpacked bits of 0,1,2,...,255
ref_bits = np.array([b for n in range(256) for b in byte_to_bits_msb(n)], dtype=np.int8)

max_bytes = 2000  # how many unpacked-bit bytes to read
filename = "debug_jul8.bin"

with open(filename, "rb") as f:
    raw = f.read(max_bytes)

data_bytes = np.frombuffer(raw, dtype=np.uint8)

# sanity check: if this is really unpacked-bit data, values should only be 0 or 1
print("unique values in data:", np.unique(data_bytes))

# map 0/1 -> -1/+1 for a real correlation peak
ref_pm1 = ref_bits.astype(np.float64) * 2 - 1
data_pm1 = data_bytes.astype(np.float64) * 2 - 1

corr = np.correlate(data_pm1, ref_pm1, mode="valid")
peak_idx = np.argmax(corr)
print("best offset:", peak_idx, "corr value:", corr[peak_idx], "/ max possible:", len(ref_pm1))

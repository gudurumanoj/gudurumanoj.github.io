"""CPU tile/addressing test and idealized global-byte model.

Run: python3 tile_model.py
Requires NumPy and Matplotlib. It does not run a GPU kernel or benchmark.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def tiled_gemm(a, b, tile):
    """Simulate one square output tile at a time, including zero-padded edges."""
    m, k = a.shape
    kb, n = b.shape
    assert k == kb and tile > 0
    out = np.zeros((m, n), dtype=np.float64)
    loads_a = loads_b = 0
    for row in range(0, m, tile):
        for col in range(0, n, tile):
            acc = np.zeros((tile, tile), dtype=np.float64)
            for depth in range(0, k, tile):
                a_tile = np.zeros((tile, tile), dtype=np.float64)
                b_tile = np.zeros((tile, tile), dtype=np.float64)
                for i in range(tile):
                    for h in range(tile):
                        if row + i < m and depth + h < k:
                            a_tile[i, h] = a[row + i, depth + h]
                            loads_a += 1
                        if depth + i < k and col + h < n:
                            b_tile[i, h] = b[depth + i, col + h]
                            loads_b += 1
                acc += a_tile @ b_tile
            rows = min(tile, m - row)
            cols = min(tile, n - col)
            out[row:row + rows, col:col + cols] = acc[:rows, :cols]
    return out, loads_a, loads_b


def ideal_bytes(m, n, k, tile, bytes_per_element=4):
    """Count valid input loads once per output tile, plus one output store."""
    loads_a = k * m * ((n + tile - 1) // tile)
    loads_b = k * n * ((m + tile - 1) // tile)
    return bytes_per_element * (loads_a + loads_b + m * n)


rng = np.random.default_rng(23)
for shape in ((5, 7, 6), (8, 8, 8), (9, 3, 11)):
    m, k, n = shape
    a = rng.normal(size=(m, k))
    b = rng.normal(size=(k, n))
    for tile in (2, 4, 8):
        got, loads_a, loads_b = tiled_gemm(a, b, tile)
        np.testing.assert_allclose(got, a @ b, rtol=1e-12, atol=1e-12)
        assert 4 * (loads_a + loads_b + m * n) == ideal_bytes(m, n, k, tile)
print("Boundary and address tests passed for 3 shapes x 3 tile sizes.")

m = n = k = 128
tiles = np.array([1, 2, 4, 8, 16, 32, 64, 128])
flops = 2 * m * n * k
intensity = np.array([flops / ideal_bytes(m, n, k, int(t)) for t in tiles])
naive_bytes = ideal_bytes(m, n, k, 1)
for tile, value in zip(tiles, intensity):
    print(f"tile={tile:3d} ideal intensity={value:6.2f} FLOP/byte "
          f"logical bytes={ideal_bytes(m, n, k, int(tile)):,}")
assert naive_bytes == 4 * (2 * m * n * k + m * n)

fig, ax = plt.subplots(figsize=(7.4, 4.2))
ax.plot(tiles, intensity, "o-", color="#a66b4f")
ax.set(xscale="log", xlabel="Square tile edge T", ylabel="Ideal logical FLOP / global byte",
       title="128³ float32 GEMM: reuse model, not measured GPU traffic")
ax.set_xticks(tiles, [str(t) for t in tiles])
ax.grid(alpha=.2)
fig.tight_layout()
fig.savefig(Path(__file__).with_name("tile-intensity.svg"))

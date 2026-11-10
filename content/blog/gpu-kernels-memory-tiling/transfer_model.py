"""Unit-safe teaching bounds for a copy/compute pipeline; no GPU is measured.

Run: python3 -B transfer_model.py
Only Python's standard library is required.
"""

GIB = 1024 ** 3  # binary gibibyte
GB = 1000 ** 3   # decimal gigabyte used in the assumed transfer rate


def copy_seconds(byte_count, effective_bytes_per_second):
    assert byte_count >= 0 and effective_bytes_per_second > 0
    return byte_count / effective_bytes_per_second


def pipeline_seconds(chunks, copy_time, compute_time):
    """Ideal two-stage flow: one copy engine, one compute engine, in order.

    Each chunk's compute waits for its own copy. Different chunks may overlap.
    This is a conditional schedule, not a performance prediction.
    """
    assert chunks >= 1 and copy_time >= 0 and compute_time >= 0
    return copy_time + compute_time + (chunks - 1) * max(copy_time, compute_time)


if __name__ == "__main__":
    payload = GIB
    assumed_rate = 25 * GB  # Assumed effective one-way host-to-device rate.
    copy_time = copy_seconds(payload, assumed_rate)
    assert abs(copy_time * 1000 - 42.94967296) < 1e-9
    assert GIB != GB
    print(f"1 GiB at assumed effective 25 GB/s: {copy_time * 1000:.2f} ms minimum copy time")

    chunks = 2
    per_chunk_copy = copy_time / chunks
    per_chunk_compute = 0.030  # Declared example assumption: 30 ms per chunk.
    serial = chunks * (per_chunk_copy + per_chunk_compute)
    ideal = pipeline_seconds(chunks, per_chunk_copy, per_chunk_compute)
    assert ideal <= serial
    assert abs(serial * 1000 - 102.94967296) < 1e-9
    assert abs(ideal * 1000 - 81.47483648) < 1e-9
    print(f"2 chunks, 30 ms compute/chunk: serial={serial * 1000:.2f} ms, "
          f"ideal two-stage schedule={ideal * 1000:.2f} ms")

"""Local TCP framing, cumulative ACK accounting, and congestion arithmetic.

Run: python3 -B network_lab.py
Optional figure: python3 -B network_lab.py --plot (requires matplotlib/numpy).
The socket experiment binds only to loopback with an ephemeral port. It checks
stream framing, NOT TCP packet boundaries, loss recovery, or congestion control.
The congestion curves are teaching formulas, NOT a TCP-stack simulation.
"""

import argparse
import math
from pathlib import Path
import queue
import socket
import struct
import threading

MAX_MESSAGE = 4096


def recv_exact(sock, count):
    out = bytearray()
    while len(out) < count:
        # Small reads deliberately exercise framing across application reads.
        chunk = sock.recv(min(3, count - len(out)))
        if not chunk:
            raise EOFError("connection closed before the complete frame arrived")
        out.extend(chunk)
    return bytes(out)


def recv_frame(sock):
    length, = struct.unpack("!I", recv_exact(sock, 4))
    if length > MAX_MESSAGE:
        raise ValueError("message exceeds the teaching protocol's size limit")
    return recv_exact(sock, length)


def frame(payload):
    if len(payload) > MAX_MESSAGE:
        raise ValueError("message too large")
    return struct.pack("!I", len(payload)) + payload


class CumulativeReceiver:
    """Byte-set model: no sequence wrap, receive-window bounds, SACK, or timers."""

    def __init__(self, next_byte):
        self.next_byte = next_byte
        self.buffered = set()

    def receive(self, sequence, length):
        if length < 0:
            raise ValueError("negative segment length")
        self.buffered.update(range(max(self.next_byte, sequence), sequence + length))
        while self.next_byte in self.buffered:
            self.buffered.remove(self.next_byte)
            self.next_byte += 1
        return self.next_byte


def cubic_target(t, previous_max=1000.0, beta=0.7, coefficient=0.4):
    """Only the cubic target after one congestion event, in segments."""
    k = (previous_max * (1 - beta) / coefficient) ** (1 / 3)
    return coefficient * (t - k) ** 3 + previous_max


def reno_rounds(rounds=48, initial=1, threshold=16, loss_at=24):
    """Idealized ACK-per-segment RTT rounds; recovery transients are omitted."""
    cwnd = initial
    out = []
    for _ in range(rounds):
        out.append(cwnd)
        if cwnd >= loss_at:
            threshold = cwnd / 2
            cwnd = threshold  # After successful fast recovery, not timeout.
        elif cwnd < threshold:
            cwnd = min(2 * cwnd, threshold)
        else:
            cwnd += 1
    return out


def loopback_check():
    errors = queue.Queue()
    payloads = [b"", "TCP is a byte stream: café".encode(), b"last message"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(5)

        def serve():
            try:
                connection, _ = listener.accept()
                with connection:
                    connection.settimeout(5)
                    for expected in payloads:
                        received = recv_frame(connection)
                        assert received == expected
                        connection.sendall(frame(received))
            except BaseException as exc:
                errors.put(exc)

        worker = threading.Thread(target=serve)
        worker.start()
        try:
            with socket.create_connection(listener.getsockname(), timeout=5) as client:
                data = b"".join(frame(payload) for payload in payloads)
                # A write can cross message boundaries. Writes are not segments.
                for start in range(0, len(data), 7):
                    client.sendall(data[start:start + 7])
                for expected in payloads:
                    assert recv_frame(client) == expected
        finally:
            worker.join(timeout=6)
        assert not worker.is_alive()
        if not errors.empty():
            raise errors.get()
    print("loopback TCP: 3 length-prefixed messages echoed correctly")


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans",
                         "svg.fonttype": "none", "svg.hashsalt": "manlog-network-v1"})
    fig, (left, right) = plt.subplots(2, 1, figsize=(9, 7), layout="constrained")
    fig.patch.set_facecolor("#fdfcf8")
    for ax in (left, right):
        ax.set_facecolor("#fdfcf8")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=.18)
    windows = reno_rounds()
    left.step(range(len(windows)), windows, where="post", color="#a66b4f")
    left.set(title="Reno-style teaching trace: ideal RTT rounds, prescribed losses",
             xlabel="Round index (fixed RTT, no recovery transients)",
             ylabel="Congestion window (segments)")
    t = np.linspace(0, 18, 250)
    k = (1000 * .3 / .4) ** (1 / 3)
    right.plot(t, cubic_target(t), color="#547b75", linewidth=2)
    right.axhline(1000, color="#817b71", linestyle="--", label="Previous maximum = 1,000")
    right.axvline(k, color="#a66b4f", linestyle=":", label=f"K = {k:.2f} s")
    right.set(title="CUBIC target alone after one loss (not a complete controller)",
              xlabel="Seconds after congestion event", ylabel="Target window (segments)")
    right.legend(fontsize=9)
    fig.savefig(Path(__file__).with_name("congestion-curves.svg"), metadata={"Date": None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    receiver = CumulativeReceiver(1001)
    acks = [receiver.receive(1401, 400), receiver.receive(1001, 400),
            receiver.receive(1001, 400), receiver.receive(1801, 100)]
    assert acks == [1001, 1801, 1801, 1901]
    print("cumulative ACK trace:", acks)
    k = (1000 * .3 / .4) ** (1 / 3)
    assert math.isclose(cubic_target(0), 700)
    assert math.isclose(cubic_target(k), 1000)
    print(f"CUBIC target: t=0 -> 700 segments; t=K={k:.3f}s -> 1000")
    bandwidth_bps, rtt_s = 250e6, .04
    bdp_bytes = bandwidth_bps * rtt_s / 8
    receive_window = 65536
    ceiling_mbps = receive_window * 8 / rtt_s / 1e6
    assert bdp_bytes == 1250000
    print(f"250 Mb/s, 40 ms: BDP={bdp_bytes:,.0f} bytes")
    print(f"64 KiB window / 40 ms: ideal window ceiling={ceiling_mbps:.3f} Mb/s")
    assert reno_rounds(6) == [1, 2, 4, 8, 16, 17]
    loopback_check()

    # Exercise framing failures without relying on packet timing or real loss.
    class ScriptedReader:
        def __init__(self, chunks): self.chunks = iter(chunks)
        def recv(self, count):
            chunk = next(self.chunks, b"")
            assert len(chunk) <= count
            return chunk
    try:
        recv_exact(ScriptedReader([b"a", b""]), 2)
        raise AssertionError("truncated stream was accepted")
    except EOFError:
        pass
    try:
        frame(b"x" * (MAX_MESSAGE + 1))
        raise AssertionError("oversized frame was accepted")
    except ValueError:
        pass
    if args.plot:
        plot()


if __name__ == "__main__":
    main()

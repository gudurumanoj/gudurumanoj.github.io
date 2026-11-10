// Single producer, single consumer, fixed-capacity queue of uint64_t values.
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <thread>

class SpscQueue {
    static constexpr std::uint64_t capacity = 8; // power of two
    std::array<std::uint64_t, capacity> slots_{};
    std::atomic<std::uint64_t> head_{0}; // next write position
    std::atomic<std::uint64_t> tail_{0}; // next read position

public:
    bool try_push(std::uint64_t value) {
        const auto head = head_.load(std::memory_order_relaxed); // producer owns it
        const auto tail = tail_.load(std::memory_order_acquire);
        if (head - tail == capacity) return false;
        slots_[head & (capacity - 1)] = value;
        head_.store(head + 1, std::memory_order_release); // publish slot
        return true;
    }

    bool try_pop(std::uint64_t& value) {
        const auto tail = tail_.load(std::memory_order_relaxed); // consumer owns it
        const auto head = head_.load(std::memory_order_acquire);
        if (head == tail) return false;
        value = slots_[tail & (capacity - 1)];
        tail_.store(tail + 1, std::memory_order_release); // return slot
        return true;
    }
};

int main() {
    constexpr std::uint64_t count = 1'000'000;
    SpscQueue queue;
    std::atomic<bool> valid{true};

    std::thread producer([&] {
        for (std::uint64_t i = 1; i <= count; ++i) {
            while (!queue.try_push(i)) std::this_thread::yield();
        }
    });
    std::thread consumer([&] {
        for (std::uint64_t expected = 1; expected <= count; ++expected) {
            std::uint64_t actual = 0;
            while (!queue.try_pop(actual)) std::this_thread::yield();
            if (actual != expected) valid.store(false, std::memory_order_relaxed);
        }
    });
    producer.join();
    consumer.join();
    if (!valid.load(std::memory_order_relaxed)) {
        std::cerr << "out-of-order or missing value\n";
        return EXIT_FAILURE;
    }
    std::cout << "received " << count << " values in order\n";
}

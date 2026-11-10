#include <cassert>
#include <condition_variable>
#include <cstddef>
#include <deque>
#include <iostream>
#include <mutex>
#include <numeric>
#include <stdexcept>
#include <thread>
#include <vector>

class BoundedQueue {
public:
    explicit BoundedQueue(std::size_t capacity) : capacity_(capacity) {
        if (capacity_ == 0) throw std::invalid_argument("capacity must be positive");
    }

    bool push(int value) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_full_.wait(lock, [&] { return closed_ || queue_.size() < capacity_; });
        if (closed_) return false;
        queue_.push_back(value);
        assert(queue_.size() <= capacity_);
        lock.unlock();
        not_empty_.notify_one();
        return true;
    }

    bool pop(int& value) {
        std::unique_lock<std::mutex> lock(mutex_);
        not_empty_.wait(lock, [&] { return closed_ || !queue_.empty(); });
        if (queue_.empty()) return false;  // Closed and drained.
        value = queue_.front();
        queue_.pop_front();
        lock.unlock();
        not_full_.notify_one();
        return true;
    }

    void close() {
        {
            std::scoped_lock<std::mutex> lock(mutex_);
            closed_ = true;
        }
        not_empty_.notify_all();
        not_full_.notify_all();
    }

private:
    const std::size_t capacity_;
    std::deque<int> queue_;
    std::mutex mutex_;
    std::condition_variable not_empty_;
    std::condition_variable not_full_;
    bool closed_ = false;  // Protected by mutex_.
};

int main() {
    constexpr int producers = 3;
    constexpr int consumers = 4;
    constexpr int per_producer = 1000;
    BoundedQueue queue(8);
    std::vector<std::thread> producer_threads;
    std::vector<std::thread> consumer_threads;
    std::vector<long long> partial_sum(consumers, 0);
    std::vector<int> partial_count(consumers, 0);

    for (int p = 0; p < producers; ++p) {
        producer_threads.emplace_back([&, p] {
            for (int i = 0; i < per_producer; ++i) {
                const bool accepted = queue.push(p * per_producer + i);
                assert(accepted);
                (void)accepted;
            }
        });
    }
    for (int c = 0; c < consumers; ++c) {
        consumer_threads.emplace_back([&, c] {
            int value;
            while (queue.pop(value)) {
                partial_sum[c] += value;
                ++partial_count[c];
            }
        });
    }

    for (auto& thread : producer_threads) thread.join();
    queue.close();
    for (auto& thread : consumer_threads) thread.join();
    const long long sum = std::accumulate(partial_sum.begin(), partial_sum.end(), 0LL);
    const int count = std::accumulate(partial_count.begin(), partial_count.end(), 0);
    constexpr long long expected = 2999LL * 3000 / 2;
    if (count != producers * per_producer || sum != expected) {
        std::cerr << "queue invariant failed\n";
        return 1;
    }
    std::cout << "consumed=" << count << ", sum=" << sum << '\n';
}

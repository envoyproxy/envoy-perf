#include "common/streaming_stats.h"

namespace Nighthawk {

StreamingStats::StreamingStats() : count_(0), mean_(0), sum_of_squares_(0) {}

void StreamingStats::addValue(int64_t value) {
  double delta, delta_n;
  count_++;
  delta = value - mean_;
  delta_n = delta / count_;
  mean_ += delta_n;
  sum_of_squares_ += delta * delta_n * (count_ - 1);
}

int64_t StreamingStats::count() const { return count_; }

double StreamingStats::mean() const { return mean_; }

double StreamingStats::variance() const { return sum_of_squares_ / (count_ - 1.0); }

double StreamingStats::stdev() const { return sqrt(variance()); }

StreamingStats StreamingStats::combine(const StreamingStats& b) {
  const StreamingStats& a = *this;
  StreamingStats combined;

  combined.count_ = a.count() + b.count();
  combined.mean_ = ((a.count() * a.mean()) + (b.count() * b.mean())) / combined.count_;
  combined.sum_of_squares_ = a.sum_of_squares_ + b.sum_of_squares_ +
                             pow(a.mean() - b.mean(), 2) * a.count() * b.count() / combined.count();
  return combined;
}

} // namespace Nighthawk
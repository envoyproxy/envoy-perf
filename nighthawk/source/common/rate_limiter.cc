#include "common/rate_limiter.h"

#include "nighthawk/common/exception.h"

namespace Nighthawk {

LinearRateLimiter::LinearRateLimiter(Envoy::TimeSource& time_source, std::chrono::nanoseconds pace)
    : RateLimiter(time_source), acquireable_count_(0), acquired_count_(0), pace_(pace),
      started_at_(time_source_.monotonicTime()) {
  if (pace.count() <= 0) {
    throw NighthawkException("The pace argument should be greater then zero.");
  }
}

bool LinearRateLimiter::tryAcquireOne() {
  if (acquireable_count_ > 0) {
    acquireable_count_--;
    acquired_count_++;
    return true;
  }

  auto elapsed_since_start = time_source_.monotonicTime() - started_at_;
  acquireable_count_ = (elapsed_since_start / pace_) - acquired_count_;
  return acquireable_count_ > 0 ? tryAcquireOne() : false;
}

void LinearRateLimiter::releaseOne() {
  acquireable_count_++;
  acquired_count_--;
}

} // namespace Nighthawk
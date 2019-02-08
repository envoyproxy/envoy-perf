#pragma once

#include "common/common/logger.h"
#include "envoy/event/timer.h"

#include "nighthawk/common/rate_limiter.h"

#include "frequency.h"

namespace Nighthawk {

// Simple rate limiter that will allow acquiring at a linear pace.
// The average rate is computed over a timeframe that starts at
// instantiation.
class LinearRateLimiter : public RateLimiter,
                          public Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  LinearRateLimiter(Envoy::TimeSource& time_source, const Frequency frequency);
  bool tryAcquireOne() override;
  void releaseOne() override;

private:
  Envoy::TimeSource& time_source_;
  int64_t acquireable_count_;
  uint64_t acquired_count_;
  const Frequency frequency_;
  const Envoy::MonotonicTime started_at_;
};

} // namespace Nighthawk
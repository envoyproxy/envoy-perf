#pragma once

#include "common/common/logger.h"

#include "envoy/common/pure.h"
#include "envoy/event/dispatcher.h"
#include "envoy/event/timer.h"
#include "envoy/runtime/runtime.h"

#include "nighthawk/common/rate_limiter.h"
#include "nighthawk/common/sequencer.h"

#include "nighthawk/source/common/statistic_impl.h"

namespace Nighthawk {

using SequencerTarget = std::function<bool(std::function<void()>)>;

class SequencerImpl : public Sequencer, public Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  SequencerImpl(Envoy::Event::Dispatcher& dispatcher, Envoy::TimeSource& time_source,
                RateLimiter& rate_limiter, SequencerTarget& target,
                std::chrono::microseconds duration, std::chrono::microseconds grace_timeout);
  void start();
  void waitForCompletion();

  // TODO(oschaaf): calling this after stop() will return broken/unexpected results.
  double completions_per_second() {
    double us =
        std::chrono::duration_cast<std::chrono::microseconds>(time_source_.monotonicTime() - start_)
            .count();

    return us == 0 ? 0 : ((targets_completed_ / us) * 1000000);
  }

  const HdrStatistic& blocked_statistic() { return blocked_statistic_; }
  const HdrStatistic& latency_statistic() { return latency_statistic_; }

  // Spinning makes tests hang when simulated time is used.
  void disable_idle_spin_for_tests() { spin_when_idle_ = false; }

protected:
  void run(bool from_timer);
  void scheduleRun();
  void stop();

private:
  static const std::chrono::milliseconds EnvoyTimerMinResolution;
  Envoy::Event::Dispatcher& dispatcher_;
  Envoy::TimeSource& time_source_;
  HdrStatistic blocked_statistic_;
  HdrStatistic latency_statistic_;
  Envoy::Event::TimerPtr periodic_timer_;
  Envoy::Event::TimerPtr incidental_timer_;
  RateLimiter& rate_limiter_;
  SequencerTarget& target_;
  std::chrono::microseconds duration_;
  std::chrono::microseconds grace_timeout_;

  Envoy::MonotonicTime start_;
  uint64_t targets_initiated_;
  uint64_t targets_completed_;
  bool spin_when_idle_;
};

} // namespace Nighthawk

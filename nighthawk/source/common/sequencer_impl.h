#pragma once

#include "common/common/logger.h"

#include "envoy/common/pure.h"
#include "envoy/event/dispatcher.h"
#include "envoy/event/timer.h"
#include "envoy/thread/thread.h"

#include "nighthawk/common/platform_util.h"
#include "nighthawk/common/rate_limiter.h"
#include "nighthawk/common/sequencer.h"

#include "nighthawk/source/common/statistic_impl.h"

namespace Nighthawk {

using SequencerTarget = std::function<bool(std::function<void()>)>;

class SequencerImpl : public Sequencer, public Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  SequencerImpl(PlatformUtil& platform_util, Envoy::Event::Dispatcher& dispatcher,
                Envoy::TimeSource& time_source, RateLimiter& rate_limiter, SequencerTarget& target,
                std::chrono::microseconds duration, std::chrono::microseconds grace_timeout);
  void start() override;
  void waitForCompletion() override;

  // TODO(oschaaf): calling this after stop() will return broken/unexpected results.
  double completionsPerSecond() const override {
    const double us =
        std::chrono::duration_cast<std::chrono::microseconds>(time_source_.monotonicTime() - start_)
            .count();

    return us == 0 ? 0 : ((targets_completed_ / us) * 1000000);
  }

  // TODO(oschaaf): we want to track time we wait between the rate limiter
  // indicating we should call target_() but target returs false, meaning
  // we are blocked / have entered closed loop mode.
  const HdrStatistic& blockedStatistic() const override { return blockedStatistic_; }
  const HdrStatistic& latencyStatistic() const override { return latencyStatistic_; }

protected:
  void run(bool from_timer);
  void scheduleRun();
  void stop();

private:
  static const std::chrono::milliseconds EnvoyTimerMinResolution;

  SequencerTarget& target_;
  PlatformUtil& platform_util_;
  Envoy::Event::Dispatcher& dispatcher_;
  Envoy::TimeSource& time_source_;
  HdrStatistic blockedStatistic_;
  HdrStatistic latencyStatistic_;
  Envoy::Event::TimerPtr periodic_timer_;
  Envoy::Event::TimerPtr incidental_timer_;
  RateLimiter& rate_limiter_;
  std::chrono::microseconds duration_;
  std::chrono::microseconds grace_timeout_;
  Envoy::MonotonicTime start_;
  uint64_t targets_initiated_;
  uint64_t targets_completed_;
};

} // namespace Nighthawk

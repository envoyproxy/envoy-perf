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

namespace {

using namespace std::chrono_literals;

constexpr std::chrono::milliseconds EnvoyTimerMinResolution = 1ms;

} // namespace

using SequencerTarget = std::function<bool(std::function<void()>)>;

/**
 * The Sequencer will drive calls to the SequencerTarget at a pace indicated by the assocated
 * RateLimiter. The contract with the target is that it will call the provided callback when it is
 * ready. The target will return true if it was able to proceed, or false if a retry is warranted at
 * a later time (because of being out of required resources, for example).
 * Note that owner of SequencerTarget must outlive the SequencerImpl to avoid use-after-free!
 */
class SequencerImpl : public Sequencer, public Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  SequencerImpl(PlatformUtil& platform_util, Envoy::Event::Dispatcher& dispatcher,
                Envoy::TimeSource& time_source, RateLimiter& rate_limiter, SequencerTarget& target,
                std::chrono::microseconds duration, std::chrono::microseconds grace_timeout);

  ~SequencerImpl() override;

  void start() override;
  void waitForCompletion() override;

  // TODO(oschaaf): calling this after stop() will return broken/unexpected results.
  double completionsPerSecond() const override {
    const double usec =
        std::chrono::duration_cast<std::chrono::microseconds>(time_source_.monotonicTime() - start_)
            .count();

    return usec == 0 ? 0 : ((targets_completed_ / usec) * 1000000);
  }

  const HdrStatistic& blockedStatistic() const override { return blocked_statistic_; }
  const HdrStatistic& latencyStatistic() const override { return latency_statistic_; }

protected:
  void run(bool from_periodic_timer);
  void scheduleRun();
  void stop(bool timed_out);
  void updateStatisticOnUnblockIfNeeded(const Envoy::MonotonicTime& now);
  void updateStartBlockingTimeIfNeeded();

private:
  SequencerTarget& target_;
  PlatformUtil& platform_util_;
  Envoy::Event::Dispatcher& dispatcher_;
  Envoy::TimeSource& time_source_;
  HdrStatistic blocked_statistic_;
  HdrStatistic latency_statistic_;
  Envoy::Event::TimerPtr periodic_timer_;
  Envoy::Event::TimerPtr spin_timer_;
  RateLimiter& rate_limiter_;
  std::chrono::microseconds duration_;
  std::chrono::microseconds grace_timeout_;
  Envoy::MonotonicTime start_;
  uint64_t targets_initiated_;
  uint64_t targets_completed_;
  bool running_;
  bool blocked_;
  Envoy::MonotonicTime blocked_start_;
};

} // namespace Nighthawk

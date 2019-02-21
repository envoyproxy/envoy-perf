#include "nighthawk/common/exception.h"

#include "common/common/assert.h"

#include "nighthawk/source/common/platform_util_impl.h"
#include "nighthawk/source/common/sequencer_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {

constexpr std::chrono::milliseconds SequencerImpl::EnvoyTimerMinResolution = 1ms;

SequencerImpl::SequencerImpl(PlatformUtil& platform_util, Envoy::Event::Dispatcher& dispatcher,
                             Envoy::TimeSource& time_source, RateLimiter& rate_limiter,
                             SequencerTarget& target, std::chrono::microseconds duration,
                             std::chrono::microseconds grace_timeout)
    : target_(target), platform_util_(platform_util), dispatcher_(dispatcher),
      time_source_(time_source), rate_limiter_(rate_limiter), duration_(duration),
      grace_timeout_(grace_timeout), start_(time_source.monotonicTime().min()),
      targets_initiated_(0), targets_completed_(0) {
  ASSERT(target_ != nullptr, "No SequencerTarget");
  periodic_timer_ = dispatcher_.createTimer([this]() { run(true); });
  incidental_timer_ = dispatcher_.createTimer([this]() { run(false); });
}

void SequencerImpl::start() {
  start_ = time_source_.monotonicTime();
  run(true);
}

void SequencerImpl::scheduleRun() { periodic_timer_->enableTimer(EnvoyTimerMinResolution); }

void SequencerImpl::stop() {
  periodic_timer_->disableTimer();
  incidental_timer_->disableTimer();
  periodic_timer_.reset(nullptr);
  incidental_timer_.reset(nullptr);
  dispatcher_.exit();
}

void SequencerImpl::run(bool from_timer) {
  const auto now = time_source_.monotonicTime();
  const auto runtime = now - start_;

  // If we exceed the benchmark duration.
  if (runtime > duration_) {
    const double rate = completionsPerSecond();

    if (targets_completed_ == targets_initiated_) {
      // All work has completed. Stop this sequencer.
      stop();
      ENVOY_LOG(
          trace,
          "SequencerImpl done processing {} operations in {} ms. (completion rate {} per second)",
          targets_completed_,
          std::chrono::duration_cast<std::chrono::milliseconds>(now - start_).count(), rate);
      return;
    } else {
      // After the benchmark duration has exceeded, we wait for a grace period for outstanding work
      // to wrap up. If that takes too long we warn about it and quit.
      if (runtime - duration_ > grace_timeout_) {
        stop();
        ENVOY_LOG(warn,
                  "SequencerImpl timeout waiting for due responses. Initiated: {} / Completed: {}. "
                  "(completion ~ rate {} per second.)",
                  targets_initiated_, targets_completed_, rate);
        return;
      }
      if (from_timer) {
        scheduleRun();
      }
    }
    return;
  }

  while (rate_limiter_.tryAcquireOne()) {
    // The rate limiter says it's OK to proceed and call the target. Let's see if the target is OK
    // with that as well.
    const bool ok = target_([this, now]() {
      auto dur = time_source_.monotonicTime() - now;
      latencyStatistic_.addValue(dur.count());
      targets_completed_++;
      // Immediately schedule us to check again, as chances are we can get on with the next task.
      incidental_timer_->enableTimer(0ms);
    });
    if (ok) {
      targets_initiated_++;
    } else {
      // This should only happen when we are running in closed-loop mode, which is always at the
      // time of writing this.
      // TODO(oschaaf): Create a specific statistic for tracking time spend here and report.
      // Measurements will be skewed.
      // The target wasn't able to proceed. Update the rate limiter, we'll try again later.
      rate_limiter_.releaseOne();
      break;
    }
  }

  if (!from_timer) {
    if (targets_initiated_ == targets_completed_) {
      // We saturated the rate limiter, and there's no outstanding work.
      // That means it looks like we are idle. Spin this event to improve
      // accuracy. As a side-effect, this may help prevent CPU frequency scaling
      // due to c-state. But on the other hand it may cause thermal throttling.
      // TODO(oschaaf): Ideally we would have much finer grained timers instead.
      // TODO(oschaaf): Optionize performing this spin loop.
      platform_util_.yieldCurrentThread();
      incidental_timer_->enableTimer(0ms);
    }
  } else {
    // Re-schedule the periodic timer if it was responsible for waking up this code.
    scheduleRun();
  }
}

void SequencerImpl::waitForCompletion() {
  dispatcher_.run(Envoy::Event::Dispatcher::RunType::Block);
}

} // namespace Nighthawk

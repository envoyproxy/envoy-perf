#include "nighthawk/common/exception.h"

#include "common/common/assert.h"

#include "nighthawk/source/common/sequencer_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {

const std::chrono::milliseconds SequencerImpl::EnvoyTimerMinResolution = 1ms;

SequencerImpl::SequencerImpl(Envoy::Event::Dispatcher& dispatcher, Envoy::TimeSource& time_source,
                             RateLimiter& rate_limiter, SequencerTarget& target,
                             std::chrono::microseconds duration,
                             std::chrono::microseconds grace_timeout)
    : dispatcher_(dispatcher), time_source_(time_source), rate_limiter_(rate_limiter),
      target_(target), duration_(duration), grace_timeout_(grace_timeout),
      start_(time_source.monotonicTime().min()), targets_initiated_(0), targets_completed_(0),
      spin_when_idle_(true) {
  if (target_ == nullptr) {
    throw NighthawkException("SequencerImpl must be constructed with a SequencerTarget.");
  }
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

  if ((now - start_) > (duration_)) {
    auto rate = completions_per_second();

    if (targets_completed_ == targets_initiated_) {
      stop();
      ENVOY_LOG(
          trace,
          "SequencerImpl done processing {} operations in {} ms. (completion rate {} per second)",
          targets_completed_,
          std::chrono::duration_cast<std::chrono::milliseconds>(now - start_).count(), rate);
      return;
    } else {
      // We wait until all due responses are in or the grace period times out.
      if (((now - start_) - duration_) > grace_timeout_) {
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
    bool ok = target_([this, now]() {
      auto dur = time_source_.monotonicTime() - now;
      latency_statistic_.addValue(dur.count());
      targets_completed_++;
      incidental_timer_->enableTimer(0ms);
    });
    if (ok) {
      targets_initiated_++;
    } else {
      // This should only happen when we are running in closed-loop mode, which is always at the
      // time of writing this.
      // TODO(oschaaf): Create a specific statistic for tracking time spend here and report.
      // Measurements will be skewed.
      rate_limiter_.releaseOne();
      break;
    }
  }

  if (!from_timer) {
    if (spin_when_idle_ && targets_initiated_ == targets_completed_) {
      // TODO(oschaaf): Ideally we would have much finer grained timers instead.
      // TODO(oschaaf): Optionize performing this spin loop.
      // We saturated the rate limiter, and there's no outstanding work.
      // That means it looks like we are idle. Spin this event to improve
      // accuracy. As a side-effect, this may help prevent CPU frequency scaling
      // due to c-state. But on the other hand it may cause thermal throttling.
      pthread_yield();
      incidental_timer_->enableTimer(0ms);
    }
  } else {
    scheduleRun();
  }
}

void SequencerImpl::waitForCompletion() {
  dispatcher_.run(Envoy::Event::Dispatcher::RunType::Block);
}

} // namespace Nighthawk

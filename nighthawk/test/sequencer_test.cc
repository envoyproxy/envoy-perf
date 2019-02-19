#include <chrono>

#include "gtest/gtest.h"

#include "test/test_common/simulated_time_system.h"

#include "common/api/api_impl.h"
#include "common/common/thread_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/stats/isolated_store_impl.h"

#include "nighthawk/common/exception.h"

#include "nighthawk/source/common/rate_limiter_impl.h"
#include "nighthawk/source/common/sequencer_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {

class SequencerTest : public testing::Test {
public:
  SequencerTest()
      : api_(1000ms /*flush interval*/, thread_factory_, store_, time_system_),
        dispatcher_(api_.allocateDispatcher()), callback_test_count_(0), frequency_(10_Hz),
        interval_(std::chrono::duration_cast<std::chrono::milliseconds>(frequency_.interval())),
        times_(5), rate_limiter_(time_system_, frequency_),
        sequencer_target_(std::bind(&SequencerTest::callback_test, this, std::placeholders::_1)),
        clock_updates_(0) {}

  void updateClock() {
    time_system_.setMonotonicTime((clock_updates_ * interval_) + interval_);
    clock_updates_++;
  }

  bool callback_test(std::function<void()> f) {
    callback_test_count_++;
    f();
    return true;
  }
  bool timeout_test(std::function<void()> /* f */) {
    callback_test_count_++;
    // We don't call f(); which will cause the sequencer to think
    // there's outstanding work.
    return true;
  }

  Envoy::Thread::ThreadFactoryImplPosix thread_factory_;
  Envoy::Stats::IsolatedStoreImpl store_;
  Envoy::Event::SimulatedTimeSystem time_system_;
  Envoy::Api::Impl api_;
  Envoy::Event::DispatcherPtr dispatcher_;
  int callback_test_count_;
  const Frequency frequency_;
  const std::chrono::milliseconds interval_;
  const uint64_t times_;
  LinearRateLimiter rate_limiter_;
  SequencerTarget sequencer_target_;
  uint64_t clock_updates_;
};

TEST_F(SequencerTest, BasicTest) {
  SequencerImpl sequencer(*dispatcher_, time_system_, rate_limiter_, sequencer_target_,
                          times_ * interval_ /* Sequencer run time.*/,
                          1ms /* Sequencer timeout. */);
  // With simulated time, this test will hang when spinning is allowed.
  sequencer.disable_idle_spin_for_tests();
  sequencer.start();

  for (uint64_t i = 0; i < times_; i++) {
    updateClock();
  }

  sequencer.waitForCompletion();
  EXPECT_EQ(times_, callback_test_count_);
  EXPECT_EQ(times_, sequencer.latency_statistic().count());
}

TEST_F(SequencerTest, TimeoutTest) {
  SequencerTarget callback = std::bind(&SequencerTest::timeout_test, this, std::placeholders::_1);
  SequencerImpl sequencer(*dispatcher_, time_system_, rate_limiter_, callback,
                          times_ * interval_ /* Sequencer run time.*/,
                          1ms /* Sequencer timeout. */);
  sequencer.disable_idle_spin_for_tests();
  sequencer.start();

  for (uint64_t i = 0; i < times_; i++) {
    updateClock();
  }

  sequencer.waitForCompletion();
  // The test is actually that we get here. We would hang
  // if the timeout didn't work. In any case, the test should have seen the callback...
  EXPECT_EQ(5, callback_test_count_);
  // ... but they ought to have not arrived at the Sequencer.
  EXPECT_EQ(0, sequencer.latency_statistic().count());
}

TEST_F(SequencerTest, EmptyCallbackThrowsTest) {
  LinearRateLimiter rate_limiter(time_system_, 10_Hz);
  SequencerTarget callback_empty;

  ASSERT_THROW(
      SequencerImpl sequencer(*dispatcher_, time_system_, rate_limiter, callback_empty, 1s, 1s),
      NighthawkException);
}

} // namespace Nighthawk

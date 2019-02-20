#include <chrono>
#include <memory>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "common/api/api_impl.h"
#include "common/common/thread_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/stats/isolated_store_impl.h"

#include "test/test_common/simulated_time_system.h"

#include "nighthawk/test/mocks.h"

#include "nighthawk/common/exception.h"
#include "nighthawk/common/platform_util.h"

#include "nighthawk/source/common/rate_limiter_impl.h"
#include "nighthawk/source/common/sequencer_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {

class SequencerIntegrationTest : public testing::Test {
public:
  SequencerIntegrationTest()
      : api_(1000ms /*flush interval*/, Envoy::Thread::ThreadFactorySingleton::get(), store_,
             time_system_),
        dispatcher_(api_.allocateDispatcher()), callback_test_count_(0), frequency_(10_Hz),
        interval_(std::chrono::duration_cast<std::chrono::milliseconds>(frequency_.interval())),
        test_number_of_intervals_(5), rate_limiter_(time_system_, frequency_),
        sequencer_target_(
            std::bind(&SequencerIntegrationTest::callback_test, this, std::placeholders::_1)),
        clock_updates_(0) {
    platform_util_.setTimeSystem(this->time_system_);
  }

  void moveClockForwardOneInterval() {
    time_system_.setMonotonicTime(time_system_.monotonicTime() + interval_);
    clock_updates_++;
  }

  bool callback_test(std::function<void()> f) {
    callback_test_count_++;
    f();
    return true;
  }
  bool timeout_test(std::function<void()> /* f */) {
    callback_test_count_++;
    // We don't call f(); which will cause the sequencer to think there is in-flight work.
    return true;
  }

  MockPlatformUtil platform_util_;
  Envoy::Stats::IsolatedStoreImpl store_;
  Envoy::Event::SimulatedTimeSystem time_system_;
  Envoy::Api::Impl api_;
  Envoy::Event::DispatcherPtr dispatcher_;
  int callback_test_count_;
  const Frequency frequency_;
  const std::chrono::milliseconds interval_;
  const uint64_t test_number_of_intervals_;
  LinearRateLimiter rate_limiter_;
  SequencerTarget sequencer_target_;
  uint64_t clock_updates_;
};

TEST_F(SequencerIntegrationTest, BasicTest) {
  SequencerImpl sequencer(
      platform_util_, *dispatcher_, time_system_, rate_limiter_, sequencer_target_,
      test_number_of_intervals_ * interval_ /* Sequencer run time.*/, 1ms /* Sequencer timeout. */);
  EXPECT_CALL(platform_util_, yieldCurrentThread())
      .Times(1 + ((test_number_of_intervals_ * interval_) - interval_) / TimeResolution);
  sequencer.start();

  // This test only needs a single update to the simulated time, after which
  // SimulatedTimeAwarePlatformUtil::yieldCurrentThread will drive time forward.
  moveClockForwardOneInterval();
  sequencer.waitForCompletion();

  EXPECT_EQ(test_number_of_intervals_, callback_test_count_);
  EXPECT_EQ(test_number_of_intervals_, sequencer.latencyStatistic().count());
}

TEST_F(SequencerIntegrationTest, TimeoutTest) {
  // We will be stepping in time at precisely the rate limiter frequency below.
  // As the callbacks won't complete, the sequencer will never consider itself idle.
  // Hence, no spinning, and no calls to yieldCurrentThread.
  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  SequencerTarget callback =
      std::bind(&SequencerIntegrationTest::timeout_test, this, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, rate_limiter_, callback,
                          test_number_of_intervals_ * interval_ /* Sequencer run time.*/,
                          1ms /* Sequencer timeout. */);
  sequencer.start();

  for (uint64_t i = 0; i < test_number_of_intervals_; i++) {
    moveClockForwardOneInterval();
  }

  sequencer.waitForCompletion();

  // The test is actually that we get here. We would hang if the timeout didn't work. In any case,
  // the test itself should have seen all callbacks...
  EXPECT_EQ(5, callback_test_count_);
  // ... but they ought to have not arrived at the Sequencer.
  EXPECT_EQ(0, sequencer.latencyStatistic().count());
}

TEST_F(SequencerIntegrationTest, EmptyCallbackAsserts) {
  LinearRateLimiter rate_limiter(time_system_, 10_Hz);
  SequencerTarget callback_empty;

  ASSERT_DEATH(SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, rate_limiter,
                                       callback_empty, 1s, 1s),
               "No SequencerTarget");
}

} // namespace Nighthawk

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

class SequencerTestBase : public testing::Test {
public:
  SequencerTestBase()
      : api_(Envoy::Thread::ThreadFactorySingleton::get(), store_, time_system_),
        dispatcher_(api_.allocateDispatcher()), callback_test_count_(0), frequency_(10_Hz),
        interval_(std::chrono::duration_cast<std::chrono::milliseconds>(frequency_.interval())),
        test_number_of_intervals_(5), sequencer_target_(std::bind(&SequencerTestBase::callback_test,
                                                                  this, std::placeholders::_1)),
        clock_updates_(0) {
    platform_util_.setTimeSystem(this->time_system_);
  }

  virtual ~SequencerTestBase() = default;

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
  bool saturated_test(std::function<void()> /* f */) { return false; }

  MockPlatformUtil platform_util_;
  Envoy::Stats::IsolatedStoreImpl store_;
  Envoy::Event::SimulatedTimeSystem time_system_;
  Envoy::Api::Impl api_;
  // TODO(oschaaf): test with MockDispatcher?
  Envoy::Event::DispatcherPtr dispatcher_;
  int callback_test_count_;
  const Frequency frequency_;
  const std::chrono::milliseconds interval_;
  const uint64_t test_number_of_intervals_;
  std::unique_ptr<RateLimiter> rate_limiter_;
  SequencerTarget sequencer_target_;
  uint64_t clock_updates_;
};

class SequencerTest : public SequencerTestBase {
public:
  SequencerTest() { rate_limiter_ = std::make_unique<MockRateLimiter>(); }
  MockRateLimiter& getRateLimiter() const { return dynamic_cast<MockRateLimiter&>(*rate_limiter_); }
};

TEST_F(SequencerTest, EmptyCallbackAsserts) {
  SequencerTarget callback_empty;

  ASSERT_DEATH(SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, getRateLimiter(),
                                       callback_empty, 1s, 1s),
               "No SequencerTarget");
}

TEST_F(SequencerTest, StartingTwiceAsserts) {
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, getRateLimiter(),
                          sequencer_target_, 1s, 1s);
  EXPECT_CALL(getRateLimiter(), tryAcquireOne());
  sequencer.start();
  ASSERT_DEATH(sequencer.start(), "");
}

TEST_F(SequencerTest, WaitButNotStartedAsserts) {
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, getRateLimiter(),
                          sequencer_target_, 1s, 1s);
  ASSERT_DEATH(sequencer.waitForCompletion(), "");
}

TEST_F(SequencerTest, RateLimiterInteraction) {
  MockSequencerTarget target;

  SequencerTarget callback =
      std::bind(&MockSequencerTarget::callback, &target, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_, callback,
                          test_number_of_intervals_ * interval_ /* Sequencer run time.*/,
                          1ms /* Sequencer timeout. */);

  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  // Have the mock rate limiter gate two calls, and block everything else.
  EXPECT_CALL(getRateLimiter(), tryAcquireOne())
      .Times(3)
      .WillOnce(testing::Return(true))
      .WillOnce(testing::Return(true))
      .WillOnce(testing::Return(false));

  EXPECT_CALL(target, callback(testing::_))
      .Times(2)
      .WillOnce(testing::Return(true))
      .WillOnce(testing::Return(true));

  sequencer.start();
  sequencer.waitForCompletion();
}

TEST_F(SequencerTest, RateLimiterSaturatedTargetInteraction) {
  MockSequencerTarget target;

  SequencerTarget callback =
      std::bind(&MockSequencerTarget::callback, &target, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_, callback,
                          test_number_of_intervals_ * interval_ /* Sequencer run time.*/,
                          1ms /* Sequencer timeout. */);

  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  // The sequencer should call RateLimiter::releaseOne() when the target returns false.
  EXPECT_CALL(getRateLimiter(), tryAcquireOne()).Times(2).WillRepeatedly(testing::Return(true));
  EXPECT_CALL(target, callback(testing::_))
      .Times(2)
      .WillOnce(testing::Return(true))
      .WillOnce(testing::Return(false));
  EXPECT_CALL(getRateLimiter(), releaseOne()).Times(1);

  sequencer.start();
  sequencer.waitForCompletion();
}

class SequencerIntegrationTest : public SequencerTestBase {
public:
  SequencerIntegrationTest() {
    rate_limiter_ = std::make_unique<LinearRateLimiter>(time_system_, frequency_);
  }
};

TEST_F(SequencerIntegrationTest, BasicTest) {
  SequencerImpl sequencer(
      platform_util_, *dispatcher_, time_system_, *rate_limiter_, sequencer_target_,
      test_number_of_intervals_ * interval_ /* Sequencer run time.*/, 1ms /* Sequencer timeout. */);
  EXPECT_CALL(platform_util_, yieldCurrentThread())
      .Times(1 + ((test_number_of_intervals_ * interval_) - interval_) / TimeResolution);

  EXPECT_EQ(0, callback_test_count_);
  EXPECT_EQ(0, sequencer.latencyStatistic().count());

  sequencer.start();

  // This test only needs a single update to the simulated time, after which
  // SimulatedTimeAwarePlatformUtil::yieldCurrentThread will drive time forward.
  moveClockForwardOneInterval();
  sequencer.waitForCompletion();

  EXPECT_EQ(test_number_of_intervals_, callback_test_count_);
  EXPECT_EQ(test_number_of_intervals_, sequencer.latencyStatistic().count());
  EXPECT_EQ(0, sequencer.blockedStatistic().count());
}

TEST_F(SequencerIntegrationTest, AlwaysSaturatedTargetTest) {
  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  SequencerTarget callback =
      std::bind(&SequencerIntegrationTest::saturated_test, this, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_, callback,
                          test_number_of_intervals_ * interval_ /* Sequencer run time.*/,
                          1ms /* Sequencer timeout. */);
  sequencer.start();

  for (uint64_t i = 0; i < test_number_of_intervals_; i++) {
    moveClockForwardOneInterval();
  }

  sequencer.waitForCompletion();
  EXPECT_EQ(0, sequencer.latencyStatistic().count());
  EXPECT_EQ(1, sequencer.blockedStatistic().count());
}

TEST_F(SequencerIntegrationTest, TimeoutTest) {
  // We will be stepping in time at precisely the rate limiter frequency below.
  // As the callbacks won't complete, the sequencer will never consider itself idle.
  // Hence, no spinning, and no calls to yieldCurrentThread.
  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  SequencerTarget callback =
      std::bind(&SequencerIntegrationTest::timeout_test, this, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_, callback,
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
  EXPECT_EQ(0, sequencer.blockedStatistic().count());
}

} // namespace Nighthawk

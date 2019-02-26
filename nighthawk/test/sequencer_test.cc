#include <chrono>
#include <memory>

#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include "common/api/api_impl.h"
#include "common/common/thread_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/stats/isolated_store_impl.h"

#include "test/mocks/event/mocks.h"
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
        dispatcher_(std::make_unique<Envoy::Event::MockDispatcher>()), callback_test_count_(0),
        frequency_(10_Hz),
        interval_(std::chrono::duration_cast<std::chrono::milliseconds>(frequency_.interval())),
        test_number_of_intervals_(5), sequencer_target_(std::bind(&SequencerTestBase::callback_test,
                                                                  this, std::placeholders::_1)),
        clock_updates_(0), timer1_set_(false), timer2_set_(false), stopped_(false) {
    platform_util_.setTimeSystem(this->time_system_);
    // When yieldCurrentThread() is called we are in a tight spin loop.
    // SimulatedTimeAwarePlatformUtil moves the simulated time forward, avoiding the tests hanging.
    setDispatcherExpectation();

    ON_CALL(platform_util_, yieldCurrentThread())
        .WillByDefault(testing::Invoke(&platform_util_, &MockPlatformUtil::yieldWithSimulatedTime));
  }

  void setDispatcherExpectation() {
    timer1_ = new testing::NiceMock<Envoy::Event::MockTimer>();
    timer2_ = new testing::NiceMock<Envoy::Event::MockTimer>();
    EXPECT_CALL(*dispatcher_, createTimer_(_))
        .WillOnce(Invoke([&](Envoy::Event::TimerCb cb) {
          timer_cb_1_ = cb;
          return timer1_;
        }))
        .WillOnce(Invoke([&](Envoy::Event::TimerCb cb) {
          timer_cb_2_ = cb;
          return timer2_;
        }));
    EXPECT_CALL(*timer1_, disableTimer()).WillOnce(Invoke([&]() { stopped_ = true; }));
    EXPECT_CALL(*timer2_, disableTimer()).WillOnce(Invoke([&]() { stopped_ = true; }));
    EXPECT_CALL(*timer1_, enableTimer(_)).WillRepeatedly(Invoke([&](std::chrono::milliseconds) {
      timer1_set_ = true;
    }));
    EXPECT_CALL(*timer2_, enableTimer(_)).WillRepeatedly(Invoke([&](std::chrono::milliseconds) {
      timer2_set_ = true;
    }));
  }

  void simulateTimerLoop() {
    while (!stopped_ && (timer1_set_ || timer2_set_)) {
      time_system_.setMonotonicTime(time_system_.monotonicTime() + 1ms);

      // timer 2 is the immediate one, which has priority.
      if (timer2_set_) {
        timer2_set_ = false;
        timer_cb_2_();
        continue;
      }

      if (timer1_set_) {
        timer1_set_ = false;
        timer_cb_1_();
        continue;
      }
    }
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
  std::unique_ptr<Envoy::Event::MockDispatcher> dispatcher_;
  int callback_test_count_;
  const Frequency frequency_;
  const std::chrono::milliseconds interval_;
  const uint64_t test_number_of_intervals_;
  std::unique_ptr<RateLimiter> rate_limiter_;
  SequencerTarget sequencer_target_;
  uint64_t clock_updates_;
  testing::NiceMock<Envoy::Event::MockTimer>* timer1_; // not owned
  testing::NiceMock<Envoy::Event::MockTimer>* timer2_; // not owned
  Envoy::Event::TimerCb timer_cb_1_;
  Envoy::Event::TimerCb timer_cb_2_;
  bool timer1_set_;
  bool timer2_set_;
  bool stopped_;
};

// For testing interaction with MockRateLimiter.
class SequencerTest : public SequencerTestBase {
public:
  SequencerTest() { rate_limiter_ = std::make_unique<MockRateLimiter>(); }
  MockRateLimiter& getRateLimiter() const { return dynamic_cast<MockRateLimiter&>(*rate_limiter_); }
};

// Test we get defined behaviour with bad input
TEST_F(SequencerTest, DISABLED_EmptyCallbackAsserts) {
  SequencerTarget callback_empty;

  ASSERT_DEATH(SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, getRateLimiter(),
                                       callback_empty, 1s, 1s),
               "No SequencerTarget");
}

// As today the Sequencer supports a single run only, we cannot start twice.
TEST_F(SequencerTest, DISABLED_StartingTwiceAsserts) {
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, getRateLimiter(),
                          sequencer_target_, 1s, 1s);
  EXPECT_CALL(getRateLimiter(), tryAcquireOne());
  sequencer.start();
  ASSERT_DEATH(sequencer.start(), "");
}

// Test the interaction with the rate limiter.
TEST_F(SequencerTest, DISABLED_RateLimiterInteraction) {
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

  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(testing::AtLeast(1));
  EXPECT_CALL(getRateLimiter(), tryAcquireOne()).Times(testing::AtLeast(1));

  sequencer.waitForCompletion();
}

// Test the interaction with a saturated rate limiter.
TEST_F(SequencerTest, DISABLED_RateLimiterSaturatedTargetInteraction) {
  MockSequencerTarget target;

  SequencerTarget callback =
      std::bind(&MockSequencerTarget::callback, &target, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_, callback,
                          test_number_of_intervals_ * interval_ /* Sequencer run time.*/,
                          0ms /* Sequencer timeout. */);
  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  // The sequencer should call RateLimiter::releaseOne() when the target returns false.
  EXPECT_CALL(getRateLimiter(), tryAcquireOne()).Times(2).WillRepeatedly(testing::Return(true));
  EXPECT_CALL(target, callback(testing::_))
      .Times(2)
      .WillOnce(testing::Return(true))
      .WillOnce(testing::Return(false));
  EXPECT_CALL(getRateLimiter(), releaseOne()).Times(1);

  sequencer.start();

  EXPECT_CALL(getRateLimiter(), tryAcquireOne()).Times(testing::AtLeast(1));
  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(testing::AtLeast(1));

  sequencer.waitForCompletion();
}

// The integration tests use a LinearRateLimiter.
class SequencerIntegrationTest : public SequencerTestBase {
public:
  SequencerIntegrationTest() {
    rate_limiter_ = std::make_unique<LinearRateLimiter>(time_system_, frequency_);
  }
};

// Test the happy flow
TEST_F(SequencerIntegrationTest, BasicTest) {
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_,
                          sequencer_target_, test_number_of_intervals_ * interval_,
                          0ms /* timeout. */);

  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(testing::AtLeast(1));
  EXPECT_CALL(*dispatcher_, run(_)).Times(1);
  EXPECT_CALL(*dispatcher_, exit()).Times(1);

  EXPECT_EQ(0, callback_test_count_);
  EXPECT_EQ(0, sequencer.latencyStatistic().count());

  sequencer.start();
  sequencer.waitForCompletion();
  while (!stopped_) {
    simulateTimerLoop();
  }

  EXPECT_EQ(test_number_of_intervals_, callback_test_count_);
  EXPECT_EQ(test_number_of_intervals_, sequencer.latencyStatistic().count());
  EXPECT_EQ(0, sequencer.blockedStatistic().count());
}

// Test an always saturated sequencer target. A concrete example would be a http benchmark client
// not being able to start any requests, for example due to misconfiguration or system conditions.
TEST_F(SequencerIntegrationTest, DISABLED_AlwaysSaturatedTargetTest) {
  // EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  SequencerTarget callback =
      std::bind(&SequencerIntegrationTest::saturated_test, this, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_, callback,
                          test_number_of_intervals_ * interval_ /* Sequencer run time.*/,
                          1ms /* Sequencer timeout. */);
  sequencer.start();
  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(2);
  sequencer.waitForCompletion();

  while (!stopped_) {
    simulateTimerLoop();
  }

  EXPECT_EQ(0, sequencer.latencyStatistic().count());
  EXPECT_EQ(1, sequencer.blockedStatistic().count());
}

// Test the (grace-)-timeout feature of the Sequencer. The used sequencer target
// (SequencerIntegrationTest::timeout_test()) will never call back, effectively simulated a
// hanging benchmark client. The actual test is that we get past sequencer.waitForCompletion(),
// which would only work when the timeout is respected.
TEST_F(SequencerIntegrationTest, DISABLED_GraceTimeoutTest) {
  // We will be stepping in time at precisely the rate limiter frequency below.
  // As the callbacks won't complete, the sequencer will never consider itself idle.
  // Hence, no spinning, and no calls to yieldCurrentThread.
  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(0);

  auto grace_timeout = 12340ms;

  SequencerTarget callback =
      std::bind(&SequencerIntegrationTest::timeout_test, this, std::placeholders::_1);
  SequencerImpl sequencer(platform_util_, *dispatcher_, time_system_, *rate_limiter_, callback,
                          test_number_of_intervals_ * interval_ /* Sequencer run time.*/,
                          grace_timeout);
  sequencer.start();

  for (uint64_t i = 0; i < test_number_of_intervals_; i++) {
    moveClockForwardOneInterval();
    dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);
    EXPECT_EQ(i + 1, callback_test_count_);
    EXPECT_EQ(0, sequencer.latencyStatistic().count());
    EXPECT_EQ(0, sequencer.blockedStatistic().count());
  }

  auto pre_timeout = time_system_.monotonicTime();

  EXPECT_CALL(platform_util_, yieldCurrentThread()).Times(testing::AtLeast(1));
  sequencer.waitForCompletion();

  auto diff = time_system_.monotonicTime() - pre_timeout;

  // + 20ms, because:
  // -- we're positioned at (test_number_of_intervals_ * interval_).
  //    the sequencer needs one more cycle to go into timeout mode, which will add 10ms.
  // -- yield() in waitForCompletion() adds 10.
  EXPECT_EQ((grace_timeout + 20ms).count(),
            std::chrono::duration_cast<std::chrono::milliseconds>(diff).count());

  // The test is actually that we get here. We would hang if the timeout didn't work. In any case,
  // the test itself should have seen all callbacks...
  EXPECT_EQ(5, callback_test_count_);
  // ... but they ought to have not arrived at the Sequencer.
  EXPECT_EQ(0, sequencer.latencyStatistic().count());
  EXPECT_EQ(0, sequencer.blockedStatistic().count());
}

} // namespace Nighthawk

#include <chrono>

#include "gtest/gtest.h"

//#include "test/test_common/simulated_time_system.h"
#include "common/event/real_time_system.h"

#include "common/api/api_impl.h"
#include "common/common/thread_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/stats/isolated_store_impl.h"

#include "nighthawk/common/exception.h"

#include "common/rate_limiter.h"
#include "common/sequencer.h"

using namespace std::chrono_literals;

namespace Nighthawk {

class SequencerTest : public testing::Test {
public:
  SequencerTest()
      : api_(1000ms /*flush interval*/, thread_factory_, store_),
        dispatcher_(api_.allocateDispatcher(time_system_)), callback_test_count_(0) {}

  bool callback_test(std::function<void()> f) {
    callback_test_count_++;
    f();
    return true;
  }

  void SetUp() { /*time_system_.setMonotonicTime(0s);*/
  }
  void TearDown() {}

  Envoy::Thread::ThreadFactoryImplPosix thread_factory_;
  Envoy::Stats::IsolatedStoreImpl store_;

  // Simulated time broke when we introduced the spin loop.
  // Figure that out at some point and restore simulated
  // time usage here.
  // Envoy::Event::SimulatedTimeSystem time_system_;
  Envoy::Event::RealTimeSystem time_system_;
  Envoy::Api::Impl api_;
  Envoy::Event::DispatcherPtr dispatcher_;
  int callback_test_count_;
};

TEST_F(SequencerTest, BasicTest) {
  LinearRateLimiter rate_limiter(time_system_, 100ms);
  SequencerTarget f = std::bind(&SequencerTest::callback_test, this, std::placeholders::_1);

  Sequencer sequencer(*dispatcher_, time_system_, rate_limiter, f, 1050ms, 1s);
  sequencer.start();
  // time_system_.setMonotonicTime(1s);
  sequencer.waitForCompletion();
  // We ought to have observed 10 callbacks at the 10/second pacing.
  EXPECT_EQ(10, callback_test_count_);
}

TEST_F(SequencerTest, EmptyCallbackThrowsTest) {
  LinearRateLimiter rate_limiter(time_system_, 100ms);
  SequencerTarget callback_empty;

  ASSERT_THROW(
      Sequencer sequencer(*dispatcher_, time_system_, rate_limiter, callback_empty, 1s, 1s),
      NighthawkException);
}

} // namespace Nighthawk

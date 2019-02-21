#pragma once

#include <chrono>
#include <memory>

#include "gmock/gmock.h"

#include "test/test_common/simulated_time_system.h"

#include "nighthawk/common/platform_util.h"
#include "nighthawk/common/rate_limiter.h"

using namespace std::chrono_literals;

namespace Nighthawk {

constexpr std::chrono::milliseconds TimeResolution = 10ms;

class SimulatedTimeAwarePlatformUtil : public PlatformUtil {
public:
  SimulatedTimeAwarePlatformUtil() : time_system_(nullptr) {}

  void yieldCurrentThread() const override {
    ASSERT(time_system_ != nullptr);
    time_system_->setMonotonicTime(time_system_->monotonicTime() + TimeResolution);
  }
  void setTimeSystem(Envoy::Event::SimulatedTimeSystem& time_system) {
    time_system_ = &time_system;
  }

private:
  Envoy::Event::SimulatedTimeSystem* time_system_;
};

class MockPlatformUtil : public PlatformUtil {
public:
  MockPlatformUtil() { delegateToSimulatedTimeAwarePlatformUtil(); }

  MOCK_CONST_METHOD0(yieldCurrentThread, void());

  void setTimeSystem(Envoy::Event::SimulatedTimeSystem& time_system) {
    simulated_time_aware_platform_util_.setTimeSystem(time_system);
  }

private:
  void delegateToSimulatedTimeAwarePlatformUtil() {
    // When this is called we are in a tight spin loop. SimulatedTimeAwarePlatformUtil moves the
    // simulated time forward, avoiding the tests hanging.
    ON_CALL(*this, yieldCurrentThread())
        .WillByDefault(testing::Invoke(&simulated_time_aware_platform_util_,
                                       &SimulatedTimeAwarePlatformUtil::yieldCurrentThread));
  }

  SimulatedTimeAwarePlatformUtil simulated_time_aware_platform_util_;
};

class MockRateLimiter : public RateLimiter {
public:
  MockRateLimiter() = default;
  MOCK_METHOD0(tryAcquireOne, bool());
  MOCK_METHOD0(releaseOne, void());
};

class FakeSequencerTarget {
public:
  virtual ~FakeSequencerTarget() = default;
  virtual bool callback(std::function<void()>) PURE;
};

class MockSequencerTarget : public FakeSequencerTarget {
public:
  MOCK_METHOD1(callback, bool(std::function<void()>));
};

} // namespace Nighthawk
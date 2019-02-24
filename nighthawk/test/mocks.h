#pragma once

#include <chrono>
#include <memory>

#include "gmock/gmock.h"

#include "test/test_common/simulated_time_system.h"

#include "nighthawk/common/platform_util.h"
#include "nighthawk/common/rate_limiter.h"

using namespace std::chrono_literals;

constexpr std::chrono::milliseconds TimeResolution = 10ms;

namespace Nighthawk {

class SimulatedTimeAwarePlatformUtil : public PlatformUtil {
public:
  SimulatedTimeAwarePlatformUtil();
  virtual ~SimulatedTimeAwarePlatformUtil();

  void yieldCurrentThread() const override;
  void setTimeSystem(Envoy::Event::SimulatedTimeSystem& time_system);

private:
  Envoy::Event::SimulatedTimeSystem* time_system_;
};

class MockPlatformUtil : public SimulatedTimeAwarePlatformUtil {
public:
  MockPlatformUtil();
  virtual ~MockPlatformUtil();

  MOCK_CONST_METHOD0(yieldCurrentThread, void());
  void yieldFromBaseClass() const;

private:
  void delegateToSimulatedTimeAwarePlatformUtil();
};

class MockRateLimiter : public RateLimiter {
public:
  MockRateLimiter();
  virtual ~MockRateLimiter();

  MOCK_METHOD0(tryAcquireOne, bool());
  MOCK_METHOD0(releaseOne, void());
};

class FakeSequencerTarget {
public:
  FakeSequencerTarget();
  virtual ~FakeSequencerTarget();
  // A fake method that matches the sequencer target signature.
  virtual bool callback(std::function<void()>) PURE;
};

class MockSequencerTarget : public FakeSequencerTarget {
public:
  MockSequencerTarget();
  virtual ~MockSequencerTarget();

  MOCK_METHOD1(callback, bool(std::function<void()>));
};

} // namespace Nighthawk
#include <chrono>
#include <memory>

#include "gmock/gmock.h"

#include "nighthawk/test/mocks.h"

using namespace std::chrono_literals;

namespace Nighthawk {

SimulatedTimeAwarePlatformUtil::SimulatedTimeAwarePlatformUtil() : time_system_(nullptr) {}

SimulatedTimeAwarePlatformUtil::~SimulatedTimeAwarePlatformUtil() = default;

void SimulatedTimeAwarePlatformUtil::yieldCurrentThread() const {
  ASSERT(time_system_ != nullptr);
  time_system_->setMonotonicTime(time_system_->monotonicTime() + TimeResolution);
}
void SimulatedTimeAwarePlatformUtil::setTimeSystem(Envoy::Event::SimulatedTimeSystem& time_system) {
  time_system_ = &time_system;
}

MockPlatformUtil::MockPlatformUtil() { delegateToSimulatedTimeAwarePlatformUtil(); }

MockPlatformUtil::~MockPlatformUtil() = default;

void MockPlatformUtil::yieldWithSimulatedTime() const {
  SimulatedTimeAwarePlatformUtil::yieldCurrentThread();
}

void MockPlatformUtil::delegateToSimulatedTimeAwarePlatformUtil() {}

MockRateLimiter::MockRateLimiter() = default;

MockRateLimiter::~MockRateLimiter() = default;

FakeSequencerTarget::FakeSequencerTarget() = default;

FakeSequencerTarget::~FakeSequencerTarget() = default;

MockSequencerTarget::MockSequencerTarget() = default;

MockSequencerTarget::~MockSequencerTarget() = default;

} // namespace Nighthawk
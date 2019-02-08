#pragma once

#include "envoy/common/pure.h"

namespace Nighthawk {

/**
 * @brief Abstract rate limiter interface
 *
 */
class RateLimiter {
public:
  virtual ~RateLimiter() = default;
  /**
   * @brief RateLimiter allows controlled acquiring of resources.
   *
   * @return true Indicates success.
   * @return false Indicates failure to acquire.
   */
  virtual bool tryAcquireOne() PURE;
  /**
   * @brief allows explicitly releasing of a controlled resource.
   *
   */
  virtual void releaseOne() PURE;
};

} // namespace Nighthawk
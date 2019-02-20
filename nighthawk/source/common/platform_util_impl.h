#pragma once

#include <pthread.h>

#include "nighthawk/common/platform_util.h"

namespace Nighthawk {

class PlatformUtilImpl : public PlatformUtil {
public:
  PlatformUtilImpl() = default;

  // TODO(oschaaf): would be nice to test this.
  void yieldCurrentThread() const override { pthread_yield(); }
};

} // namespace Nighthawk
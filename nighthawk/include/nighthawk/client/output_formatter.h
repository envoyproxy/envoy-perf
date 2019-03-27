#pragma once

#include <memory>

#include "envoy/common/pure.h"

#include "nighthawk/client/benchmark_client.h"
#include "nighthawk/client/options.h"
#include "nighthawk/common/statistic.h"

namespace Nighthawk {
namespace Client {

class OutputFormatter {
public:
  virtual ~OutputFormatter() = default;
  virtual std::string toString() const PURE;
  virtual void writeToFile(std::string path) const PURE;
};

} // namespace Client
} // namespace Nighthawk

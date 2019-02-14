#pragma once

#include <cstdint>
#include <memory>
#include <string>

#include "common/common/non_copyable.h"
#include "envoy/common/pure.h"

#include "nighthawk/source/client/output.pb.h"

namespace Nighthawk {

/**
 * Abstract interface for a statistic.
 */
class Statistic : Envoy::NonCopyable {
public:
  virtual ~Statistic() = default;
  /**
   * Method for adding a sample value.
   * @param value the value of the sample to add
   */
  virtual void addValue(int64_t sample_value) PURE;

  virtual uint64_t count() const PURE;
  virtual double mean() const PURE;
  virtual double variance() const PURE;
  virtual double stdev() const PURE;

  /**
   * Only used in tests to match expectations to the right precision level.
   * @return Number of significant digits. 0 is assumed to be max precision.
   */
  virtual uint64_t significant_digits() const { return 0; }

  /**
   * Dumps a representation of the statistic in plain text to stdout.
   */
  virtual void dumpToStdOut(const std::string& header) const PURE;

  /**
   * Updates the proto output to reflect the contents of the statistic.
   */
  virtual void toProtoOutput(nighthawk::client::Output& output) PURE;

  /**
   * Combines two Statistics into one, and returns a new, merged, Statistic.
   * This is useful for computing results from multiple workers into a
   * single global view.
   * @param a The Statistic that should be combined with this instance.
   * @return T Merged Statistic instance.
   */
  virtual std::unique_ptr<Statistic> combine(const Statistic& a) PURE;
};

} // namespace Nighthawk
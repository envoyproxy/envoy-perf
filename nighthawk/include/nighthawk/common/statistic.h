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
  virtual double pvariance() const PURE;
  virtual double pstdev() const PURE;

  /**
   * Only used in tests to match expectations to the right precision level.
   * @return Number of significant digits. 0 is assumed to be max precision.
   */
  virtual uint64_t significantDigits() const { return 0; }

  /**
   * Indicates if the implementation is subject to catastrophic cancellation.
   * Used in tests.
   * @return True iff catastrophic cancellation should not occur.
   */
  virtual bool resistsCatastrophicCancellation() const { return false; }

  /**
   * Gets a representation of the statistic as a std::string.
   */
  virtual std::string toString() const PURE;

  /**
   * Gets a proto Output reflecting the contents of the statistic.
   */
  virtual nighthawk::client::Statistic toProto() PURE;

  /**
   * Combines two Statistics into one, and returns a new, merged, Statistic.
   * This is useful for computing results from multiple workers into a
   * single global view. Types of the Statistics objects that will be combined
   * must be the same, or else a std::bad_cast exception will be raised.
   * @param statistic The Statistic that should be combined with this instance.
   * @return T Merged Statistic instance.
   */
  virtual std::unique_ptr<Statistic> combine(const Statistic& statistic) PURE;
};

} // namespace Nighthawk
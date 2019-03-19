#pragma once

#include <functional>
#include <memory>

#include "envoy/runtime/runtime.h"

#include "nighthawk/common/statistic.h"

namespace Nighthawk {
namespace Client {

typedef std::function<bool(const std::string, const uint64_t)> CounterFilter;

class BenchmarkClient {
public:
  virtual ~BenchmarkClient() = default;

  /**
   * Initialize will be called on the worker thread after it has started.
   * @param runtime to be used during initialization.
   */
  virtual bool initialize(Envoy::Runtime::Loader& runtime) PURE;

  /**
   * Terminate will be called on the worker thread before it ends.
   */
  virtual void terminate() PURE;

  /**
   * Turns latency measurement on or off.
   *
   * @param measure_latencies true iff latencies should be measured.
   */
  virtual void setMeasureLatencies(bool measure_latencies) PURE;

  /**
   * Gets the statistics, keyed by id.
   * @return StatisticPtrMap A map of Statistics keyed by id.
   */
  virtual StatisticPtrMap statistics() const PURE;

  /**
   * Tries to start a request. In open-loop mode this MUST always return true.
   *
   * @param caller_completion_callback The callback the client must call back upon completion of a
   * successfully started request.
   *
   * @return true if the request could be started.
   * @return false if the request could not be started, for example due to resource limits.
   */
  virtual bool tryStartOne(std::function<void()> caller_completion_callback) PURE;

  /**
   * Transforms statistics matching the filter argument into a string of statistic "name:value"
   * pairs, one per line.
   * @param filter function that returns true iff a statistic should be transformed, based on the
   * named and value it gets passed.
   * @return std::string containing zero or more lines containing "name:value\n".
   */
  virtual std::string countersToString(CounterFilter filter) const PURE;

  /**
   * Determines if latency measurement is on.
   *
   * @return bool indicating if latency measurement is enabled.
   */
  virtual bool measureLatencies() const PURE;
};

typedef std::unique_ptr<BenchmarkClient> BenchmarkClientPtr;

} // namespace Client
} // namespace Nighthawk
#pragma once

#include <memory>

#include "envoy/common/pure.h"

#include "nighthawk/client/benchmark_client.h"
#include "nighthawk/common/statistic.h"
#include "nighthawk/common/worker.h"

namespace Nighthawk {
namespace Client {

/**
 * Interface for a threaded benchmark client worker.
 */
class ClientWorker : virtual public Worker {
public:
  /**
   * Gets the statistics, keyed by id.
   * @return StatisticPtrMap A map of Statistics keyed by id.
   */
  virtual StatisticPtrMap statistics() const PURE;

  virtual const BenchmarkClient& benchmark_client() const PURE;

  /**
   * @brief Returns true iff the worker ran and completed successfully.
   *
   * @return true If the work that was performed was successfully completed.
   * @return false If the work that was performed was not succesfully completed.
   */
  virtual bool success() const PURE;
};

typedef std::unique_ptr<ClientWorker> ClientWorkerPtr;

} // namespace Client
} // namespace Nighthawk

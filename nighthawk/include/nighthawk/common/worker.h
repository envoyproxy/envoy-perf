#pragma once

#include <memory>

#include "envoy/common/pure.h"

#include "nighthawk/common/statistic.h"

namespace Nighthawk {

/**
 * Interface for a threaded worker.
 */
class Worker {
public:
  virtual ~Worker() {}

  /**
   * Start the worker thread.
   */
  virtual void start() PURE;

  /**
   * Wait for the worker thread to complete its work.
   */
  virtual void waitForCompletion() PURE;

protected:
  /**
   * Perform the actual work on the associated thread initiated by start().
   */
  virtual void work() PURE;
};

typedef std::unique_ptr<Worker> WorkerPtr;

} // namespace Nighthawk

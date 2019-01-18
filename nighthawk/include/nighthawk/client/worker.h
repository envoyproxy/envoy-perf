#pragma once

#include <memory>

namespace Nighthawk {
namespace Client {

/**
 * Interface for a threaded benchmark client worker. All routines are thread safe.
 */
class Worker {
public:
  virtual ~Worker() {}

  /**
   * Start the worker thread.
   */
  // TODO(oschaaf): Guarddog?
  virtual void start() PURE;

  /**
   * Stop the worker thread.
   */
  virtual void stop() PURE;
};

typedef std::unique_ptr<Worker> WorkerPtr;

/**
 * Factory for creating workers.
 */
class WorkerFactory {
public:
  virtual ~WorkerFactory() {}

  /**
   * @return WorkerPtr a new worker.
   */
  virtual WorkerPtr createWorker() PURE;
};

} // namespace Client
} // namespace Nighthawk

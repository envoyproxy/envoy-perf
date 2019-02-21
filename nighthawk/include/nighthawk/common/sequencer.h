#pragma once

#include <functional>

#include "envoy/common/pure.h"

#include "nighthawk/common/statistic.h"

namespace Nighthawk {

/**
 * Abstract Sequencer interface. The Sequencer will drive calls to the SequencerTarget.
 * The contract with the target is that it will call the provided callback when it is ready.
 * The target will return true if it was able to proceed, or false if a retry is warranted at
 * a later time (because of being out of required resources, for example).
 */
class Sequencer {
public:
  virtual ~Sequencer() = default;

  /**
   * Starts the sequencer.
   */
  virtual void start() PURE;

  /**
   * Wait until the sequencer has finished.
   */
  virtual void waitForCompletion() PURE;

  /**
   * @return double an up-to-date completions per second rate.
   */
  virtual double completionsPerSecond() const PURE;

  /**
   * @return const Statistic& tracks time spend waiting on SequencerTarget while it returns false.
   * (In other words, time spend while the Sequencer is idle and not blocked by other factors, like
   * a rate limiter)
   */
  virtual const Statistic& blockedStatistic() const PURE;

  /**
   * @return const Statistic& tracks latency between calling the SequencerTarget and observing its
   * callback.
   */
  virtual const Statistic& latencyStatistic() const PURE;
};

} // namespace Nighthawk
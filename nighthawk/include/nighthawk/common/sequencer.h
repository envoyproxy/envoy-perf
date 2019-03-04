#pragma once

#include <functional>

#include "envoy/common/pure.h"

#include "nighthawk/common/statistic.h"

namespace Nighthawk {

/**
 * Abstract Sequencer interface.
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
   * (In other words, time spend while the Sequencer is idle and not blocked by a rate limiter)
   */
  virtual const Statistic& blockedStatistic() const PURE;

  /**
   * @return const Statistic& tracks latency between calling the SequencerTarget and observing its
   * callback.
   */
  virtual const Statistic& latencyStatistic() const PURE;
};

} // namespace Nighthawk
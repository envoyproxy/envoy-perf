#pragma once

#include <memory>

#include "envoy/common/pure.h"
#include "envoy/common/time.h"

#include "envoy/api/api.h"
#include "envoy/common/time.h"
#include "envoy/event/dispatcher.h"
#include "envoy/stats/store.h"

#include "nighthawk/client/benchmark_client.h"
#include "nighthawk/client/options.h"
#include "nighthawk/common/platform_util.h"
#include "nighthawk/common/sequencer.h"
#include "nighthawk/common/statistic.h"
#include "nighthawk/source/common/utility.h"

namespace Nighthawk {
namespace Client {

/**
 * Factory-like construct, responsible for construction of a few classes/instances where it is
 * expected configuration needs to be applied. Helps with keeping includes to just the interfaces in
 * other places and mostly translating incoming configuration to class fields in once place. Will
 * probably be decomposed into real factory constructs later on.
 */
class OptionInterpreter {
public:
  virtual ~OptionInterpreter() = default;
  virtual BenchmarkClientPtr createBenchmarkClient(Envoy::Api::Api& api,
                                                   Envoy::Event::Dispatcher& dispatcher,
                                                   Envoy::Stats::Store& store,
                                                   const Uri uri) const PURE;

  virtual Envoy::Stats::StorePtr createStatsStore() const PURE;
  virtual StatisticPtr createStatistic() const PURE;
  virtual PlatformUtilPtr getPlatformUtil() const PURE;
  virtual SequencerPtr createSequencer(Envoy::TimeSource& time_source,
                                       Envoy::Event::Dispatcher& dispatcher,
                                       BenchmarkClient& benchmark_client) const PURE;
};

typedef std::unique_ptr<OptionInterpreter> OptionInterpreterPtr;

} // namespace Client
} // namespace Nighthawk

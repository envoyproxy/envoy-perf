#pragma once

#include "nighthawk/client/option_interpreter.h"

#include "envoy/api/api.h"
#include "envoy/event/dispatcher.h"
#include "envoy/stats/store.h"

#include "nighthawk/source/common/platform_util_impl.h"

namespace Nighthawk {
namespace Client {

class OptionInterpreterImpl : public OptionInterpreter {
public:
  OptionInterpreterImpl(const Options& options);
  BenchmarkClientPtr createBenchmarkClient(Envoy::Api::Api& api,
                                           Envoy::Event::Dispatcher& dispatcher) const override;
  SequencerPtr createSequencer(Envoy::TimeSource& time_source, Envoy::Event::Dispatcher& dispatcher,
                               BenchmarkClient& benchmark_client) const override;

  Envoy::Stats::StorePtr createStatsStore() const override;
  StatisticPtr createStatistic() const override;
  // TODO(oschaaf): revisit, do we want a singleton here?
  PlatformUtilPtr getPlatformUtil() const override;

private:
  const Options& options_;
  PlatformUtilImpl platform_util_;
};

} // namespace Client
} // namespace Nighthawk

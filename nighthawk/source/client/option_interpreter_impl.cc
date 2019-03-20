#include "nighthawk/source/client/option_interpreter_impl.h"

#include "common/stats/isolated_store_impl.h"

#include "nighthawk/source/client/benchmark_client_impl.h"
#include "nighthawk/source/common/platform_util_impl.h"
#include "nighthawk/source/common/rate_limiter_impl.h"
#include "nighthawk/source/common/sequencer_impl.h"
#include "nighthawk/source/common/statistic_impl.h"

namespace Nighthawk {
namespace Client {

OptionInterpreterImpl::OptionInterpreterImpl(const Options& options) : options_(options) {}

BenchmarkClientPtr
OptionInterpreterImpl::createBenchmarkClient(Envoy::Api::Api& api,
                                             Envoy::Event::Dispatcher& dispatcher) const {
  auto benchmark_client = std::make_unique<BenchmarkClientHttpImpl>(
      api, dispatcher, createStatsStore(), createStatistic(), createStatistic(), options_.uri(),
      options_.h2());
  benchmark_client->setConnectionTimeout(options_.timeout());
  benchmark_client->setConnectionLimit(options_.connections());
  return benchmark_client;
};

SequencerPtr OptionInterpreterImpl::createSequencer(Envoy::TimeSource& time_source,
                                                    Envoy::Event::Dispatcher& dispatcher,
                                                    BenchmarkClient& benchmark_client) const {
  RateLimiterPtr rate_limiter =
      std::make_unique<LinearRateLimiter>(time_source, Frequency(options_.requests_per_second()));
  SequencerTarget sequencer_target =
      std::bind(&BenchmarkClient::tryStartOne, &benchmark_client, std::placeholders::_1);

  SequencerPtr sequencer = std::make_unique<SequencerImpl>(
      platform_util_, dispatcher, time_source, std::move(rate_limiter), sequencer_target,
      createStatistic(), createStatistic(), options_.duration(), options_.timeout());
  return sequencer;
}

Envoy::Stats::StorePtr OptionInterpreterImpl::createStatsStore() const {
  return std::make_unique<Envoy::Stats::IsolatedStoreImpl>();
}

StatisticPtr OptionInterpreterImpl::createStatistic() const {
  return std::make_unique<HdrStatistic>();
}

PlatformUtilPtr OptionInterpreterImpl::getPlatformUtil() const {
  // TODO(oschaaf): singleton?
  return std::make_unique<PlatformUtilImpl>();
}

} // namespace Client
} // namespace Nighthawk

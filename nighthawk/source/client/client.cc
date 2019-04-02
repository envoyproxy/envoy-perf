#include "nighthawk/source/client/client.h"

#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <random>

#include "ares.h"

#include "envoy/stats/store.h"

#include "common/api/api_impl.h"
#include "common/common/thread_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/event/real_time_system.h"
#include "common/filesystem/filesystem_impl.h"
#include "common/network/utility.h"
#include "common/runtime/runtime_impl.h"
#include "common/thread_local/thread_local_impl.h"

#include "nighthawk/source/client/client_worker_impl.h"
#include "nighthawk/source/client/factories_impl.h"
#include "nighthawk/source/client/options_impl.h"
#include "nighthawk/source/client/output.pb.h"
#include "nighthawk/source/client/output_formatter_impl.h"
#include "nighthawk/source/common/frequency.h"
#include "nighthawk/source/common/utility.h"

using namespace std::chrono_literals;

namespace Nighthawk {
namespace Client {

Main::Main(int argc, const char* const* argv)
    : Main(std::make_unique<Client::OptionsImpl>(argc, argv)) {}

Main::Main(Client::OptionsPtr&& options) : options_(std::move(options)) {
  ares_library_init(ARES_LIB_INIT_ALL);
  Envoy::Event::Libevent::Global::initialize();
  configureComponentLogLevels(spdlog::level::from_str(options_->verbosity()));
}

Main::~Main() { ares_library_cleanup(); }

void Main::configureComponentLogLevels(spdlog::level::level_enum level) {
  // TODO(oschaaf): Add options to tweak the log level of the various log tags
  // that are available.
  Envoy::Logger::Registry::setLogLevel(level);
  Envoy::Logger::Logger* logger_to_change = Envoy::Logger::Registry::logger("main");
  logger_to_change->setLevel(level);
}

uint32_t Main::determineConcurrency() const {
  uint32_t cpu_cores_with_affinity = PlatformUtils::determineCpuCoresWithAffinity();
  if (cpu_cores_with_affinity == 0) {
    ENVOY_LOG(warn, "Failed to determine the number of cpus with affinity to our thread.");
    cpu_cores_with_affinity = std::thread::hardware_concurrency();
  }

  bool autoscale = options_->concurrency() == "auto";
  // TODO(oschaaf): Maybe, in the case where the concurrency flag is left out, but
  // affinity is set / we don't have affinity with all cores, we should default to autoscale.
  // (e.g. we are called via taskset).
  uint32_t concurrency = autoscale ? cpu_cores_with_affinity : std::stoi(options_->concurrency());

  if (autoscale) {
    ENVOY_LOG(info, "Detected {} (v)CPUs with affinity..", cpu_cores_with_affinity);
  }

  ENVOY_LOG(info, "Starting {} threads / event loops. Test duration: {} seconds.", concurrency,
            options_->duration().count());
  ENVOY_LOG(info, "Global targets: {} connections and {} calls per second.",
            options_->connections() * concurrency, options_->requests_per_second() * concurrency);

  if (concurrency > 1) {
    ENVOY_LOG(info, "   (Per-worker targets: {} connections and {} calls per second)",
              options_->connections(), options_->requests_per_second());
  }

  return concurrency;
}

std::vector<StatisticPtr>
Main::mergeWorkerStatistics(const StatisticFactory& statistic_factory,
                            const std::vector<ClientWorkerPtr>& workers) const {
  std::vector<StatisticPtr> merged_statistics;
  StatisticPtrMap w0_statistics = workers[0]->statistics();
  for (auto w0_statistic : w0_statistics) {
    auto new_statistic = statistic_factory.create();
    new_statistic->setId(w0_statistic.first);
    merged_statistics.push_back(std::move(new_statistic));
  }

  for (auto& w : workers) {
    uint32_t i = 0;
    for (auto wx_statistic : w->statistics()) {
      auto merged = merged_statistics[i]->combine(*(wx_statistic.second));
      merged->setId(merged_statistics[i]->id());
      merged_statistics[i] = std::move(merged);
      i++;
    }
  }
  return merged_statistics;
}

std::map<std::string, uint64_t>
Main::mergeWorkerCounters(const std::vector<ClientWorkerPtr>& workers) const {
  std::map<std::string, uint64_t> merged;

  Utility util;
  for (auto& w : workers) {
    auto counters = util.mapCountersFromStore(
        w->store(), [](std::string, uint64_t value) { return value > 0; });
    for (auto counter : counters) {
      if (merged.count(counter.first) == 0) {
        merged[counter.first] = counter.second;
      } else {
        merged[counter.first] += counter.second;
      }
    }
  }

  return merged;
}

bool Main::runWorkers(const BenchmarkClientFactory& benchmark_client_factory,
                      const SequencerFactory& sequencer_factory,
                      std::vector<StatisticPtr>& merged_statistics,
                      std::map<std::string, uint64_t>& merged_counters) const {
  auto thread_factory = Envoy::Thread::ThreadFactoryImplPosix();
  StoreFactoryImpl store_factory(*options_);
  StatisticFactoryImpl statistic_factory(*options_);
  Envoy::Stats::StorePtr store = store_factory.create();
  Envoy::Event::RealTimeSystem time_system;
  Envoy::Filesystem::InstanceImplPosix filesystem;
  Envoy::Api::Impl api(thread_factory, *store, time_system, filesystem);
  Envoy::ThreadLocal::InstanceImpl tls;
  Envoy::Event::DispatcherPtr main_dispatcher(api.allocateDispatcher());
  Uri uri = Uri::Parse(options_->uri());
  tls.registerThread(*main_dispatcher, true);
  try {
    // TODO(oschaaf): verify with @htuch that ::Auto is the right default here.
    // Also, this should be optionized.
    uri.resolve(*main_dispatcher, Envoy::Network::DnsLookupFamily::Auto);
  } catch (const UriException) {
    tls.shutdownGlobalThreading();
    return false;
  }

  uint32_t concurrency = determineConcurrency();
  std::vector<ClientWorkerPtr> workers;
  // We try to offset the start of each thread so that workers will execute tasks evenly spaced in
  // time.
  // TODO(oschaaf): Expose the hard-coded two seconds below in configuration.
  auto first_worker_start = time_system.monotonicTime() + 2s;
  double inter_worker_delay_usec = (1. / options_->requests_per_second()) * 1000000 / concurrency;

  for (uint32_t worker_number = 0; worker_number < concurrency; worker_number++) {
    auto worker_delay = std::chrono::duration_cast<std::chrono::nanoseconds>(
        ((inter_worker_delay_usec * worker_number) * 1us));
    workers.push_back(std::make_unique<ClientWorkerImpl>(
        api, tls, benchmark_client_factory, sequencer_factory, uri, store_factory.create(),
        worker_number, first_worker_start + worker_delay));
  }

  Envoy::Runtime::RandomGeneratorImpl generator;
  Envoy::Runtime::ScopedLoaderSingleton loader(
      Envoy::Runtime::LoaderPtr{new Envoy::Runtime::LoaderImpl(generator, *store, tls)});

  for (auto& w : workers) {
    w->start();
  }

  bool ok = true;
  for (auto& w : workers) {
    w->waitForCompletion();
    ok = ok && w->success();
  }
  if (ok) {
    merged_statistics = mergeWorkerStatistics(statistic_factory, workers);
    merged_counters = mergeWorkerCounters(workers);
  }

  tls.shutdownGlobalThreading();
  return ok;
}

bool Main::run() {
  Envoy::Thread::MutexBasicLockable log_lock;
  std::vector<StatisticPtr> merged_statistics;
  std::map<std::string, uint64_t> merged_counters;
  auto logging_context = std::make_unique<Envoy::Logger::Context>(
      spdlog::level::from_str(options_->verbosity()), "[%T.%f][%t][%L] %v", log_lock);
  BenchmarkClientFactoryImpl benchmark_client_factory(*options_);
  SequencerFactoryImpl sequencer_factory(*options_);

  std::cout << "Nighthawk - A layer 7 protocol benchmarking tool.\n";

  if (runWorkers(benchmark_client_factory, sequencer_factory, merged_statistics, merged_counters)) {
    Envoy::RealTimeSource time_source;
    ConsoleOutputFormatterImpl console_formatter(time_source, *options_, merged_statistics,
                                                 merged_counters);
    // TODO(oschaaf): output format, location, method, etc should be optionized.
    std::cout << console_formatter.toString();
    JsonOutputFormatterImpl json_formatter(time_source, *options_, merged_statistics,
                                           merged_counters);
    mkdir("measurements", 0777);
    std::ofstream stream;
    const int64_t epoch_seconds = time_source.systemTime().time_since_epoch().count();
    std::string filename = fmt::format("measurements/{}.json", epoch_seconds);
    stream.open(filename);
    stream << json_formatter.toString();
    ENVOY_LOG(info, "Done. Wrote {}.", filename);
    return true;
  } else {
    std::cerr << "An error occurred";
  }

  return false;
}

} // namespace Client
} // namespace Nighthawk

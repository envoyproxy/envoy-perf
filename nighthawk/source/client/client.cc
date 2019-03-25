#include "nighthawk/source/client/client.h"

#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <random>

#include "ares.h"
#include <google/protobuf/util/json_util.h>

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
#include "nighthawk/source/client/option_interpreter_impl.h"
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
  // We rely on Envoy's logging infra.
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

void Main::outputCliStats(const std::vector<StatisticPtr>& merged_statistics) const {
  std::string cli_result = "Merged statistics:\n{}";
  for (auto& statistic : merged_statistics) {
    cli_result = fmt::format(cli_result, statistic->id() + "\n{}");
    cli_result = fmt::format(cli_result, statistic->toString() + "\n{}");
  }
  cli_result = fmt::format(cli_result, "");
  ENVOY_LOG(info, "{}", cli_result);
}

std::vector<StatisticPtr>
Main::mergeWorkerStatistics(const OptionInterpreter& option_interpreter,
                            const std::vector<ClientWorkerPtr>& workers) const {
  std::vector<StatisticPtr> merged_statistics;
  StatisticPtrMap w0_statistics = workers[0]->statistics();
  for (auto w0_statistic : w0_statistics) {
    auto new_statistic = option_interpreter.createStatistic();
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

bool Main::runWorkers(OptionInterpreter& option_interpreter,
                      std::vector<StatisticPtr>& merged_statistics) const {
  auto thread_factory = Envoy::Thread::ThreadFactoryImplPosix();
  Envoy::Stats::StorePtr store = option_interpreter.createStatsStore();
  Envoy::Event::RealTimeSystem time_system;
  Envoy::Filesystem::InstanceImplPosix filesystem;

  Envoy::Api::Impl api(thread_factory, *store, time_system, filesystem);
  Envoy::ThreadLocal::InstanceImpl tls;
  Envoy::Event::DispatcherPtr main_dispatcher(api.allocateDispatcher());
  Uri uri = Uri::Parse(options_->uri());
  tls.registerThread(*main_dispatcher, true);
  try {
    uri.resolve(*main_dispatcher, Envoy::Network::DnsLookupFamily::Auto);
  } catch (const UriException) {
    tls.shutdownGlobalThreading();
    return false;
  }

  uint32_t concurrency = determineConcurrency();
  // We try to offset the start of each thread so that workers will execute tasks evenly
  // spaced in time.
  // E.g.if we have a 10 workers at 10k/second our global pacing is 100k/second (or 1 / 100 usec).
  // We would then offset the worker starts like [0usec, 10 usec, ..., 90 usec].
  double inter_worker_delay_usec = (1. / options_->requests_per_second()) * 1000000 / concurrency;

  // We're going to fire up #concurrency benchmark loops and wait for them to complete.
  std::vector<ClientWorkerPtr> workers;
  for (uint32_t worker_number = 0; worker_number < concurrency; worker_number++) {
    workers.push_back(std::make_unique<ClientWorkerImpl>(
        option_interpreter, api, tls, uri, option_interpreter.createStatsStore(), worker_number,
        inter_worker_delay_usec * worker_number));
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
  tls.shutdownGlobalThreading();
  if (ok) {
    merged_statistics = mergeWorkerStatistics(option_interpreter, workers);
  }
  return ok;
}

bool Main::run() {
  Envoy::Thread::MutexBasicLockable log_lock;
  auto logging_context = std::make_unique<Envoy::Logger::Context>(
      spdlog::level::from_str(options_->verbosity()), "[%T.%f][%t][%L] %v", log_lock);

  OptionInterpreterImpl option_interpreter(*options_);

  std::vector<StatisticPtr> merged_statistics;
  bool ok;
  try {
    ok = runWorkers(option_interpreter, merged_statistics);
  } catch (UriException) {
    ok = false;
  }
  if (ok) {
    outputCliStats(merged_statistics);
    // Output the statistics to the proto
    nighthawk::client::Output output;
    output.set_allocated_options(options_->toCommandLineOptions().release());

    struct timeval tv;
    gettimeofday(&tv, NULL);
    output.mutable_timestamp()->set_seconds(tv.tv_sec);
    output.mutable_timestamp()->set_nanos(tv.tv_usec * 1000);

    for (auto& statistic : merged_statistics) {
      auto result = output.add_results();
      result->set_name("global");
      *(result->add_statistics()) = statistic->toProto();
      // TODO(oschaaf): summed per-worker counters
    }

    std::string str;
    google::protobuf::util::JsonPrintOptions options;
    google::protobuf::util::MessageToJsonString(output, &str, options);

    mkdir("measurements", 0777);
    std::ofstream stream;
    int64_t epoch_seconds = std::chrono::system_clock::now().time_since_epoch().count();
    std::string filename = fmt::format("measurements/{}.json", epoch_seconds);
    stream.open(filename);
    stream << str;
    ENVOY_LOG(info, "Done. Wrote {}.", filename);
  } else {
    ENVOY_LOG(error, "Error occurred.");
  }

  return ok;
}

} // namespace Client
} // namespace Nighthawk

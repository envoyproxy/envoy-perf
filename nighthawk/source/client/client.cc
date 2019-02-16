#include "nighthawk/source/client/client.h"

#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <random>

#include "ares.h"
#include <google/protobuf/util/json_util.h>

#include "common/api/api_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/event/real_time_system.h"
#include "common/network/utility.h"

#include "nighthawk/source/client/options_impl.h"
#include "nighthawk/source/client/output.pb.h"
#include "nighthawk/source/client/output_formatter_impl.h"
#include "nighthawk/source/client/worker_impl.h"
#include "nighthawk/source/common/frequency.h"
#include "nighthawk/source/common/statistic_impl.h"
#include "nighthawk/source/common/utility.h"

using namespace std::chrono_literals;

namespace Nighthawk {
namespace Client {

Main::Main(int argc, const char* const* argv)
    : Main(std::make_unique<Client::OptionsImpl>(argc, argv)) {}

Main::Main(Client::OptionsPtr&& options)
    : options_(std::move(options)), time_system_(std::make_unique<Envoy::Event::RealTimeSystem>()) {
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

bool Main::run() {
  // TODO(oschaaf): platform specificity need addressing.
  auto thread_factory = Envoy::Thread::ThreadFactoryImplPosix();
  Envoy::Thread::MutexBasicLockable log_lock;
  auto logging_context = std::make_unique<Envoy::Logger::Context>(
      spdlog::level::from_str(options_->verbosity()), "[%T.%f][%t][%L] %v", log_lock);

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

  // We're going to fire up #concurrency benchmark loops and wait for them to complete.
  std::vector<WorkerImplPtr> workers;
  for (uint32_t i = 0; i < concurrency; i++) {
    workers.push_back(std::make_unique<WorkerImpl>(thread_factory, *options_, i));
    workers[i]->start();
  }

  std::unique_ptr<Statistic> merged_statistics = std::make_unique<HdrStatistic>();
  for (auto& w : workers) {
    w->waitForCompletion();
    merged_statistics = merged_statistics->combine(w->statistic());
  }
  workers.clear();

  ENVOY_LOG(info, "{}", concurrency > 1 ? "X-Thread statistics" : "Statistics");
  ENVOY_LOG(info, "{}", merged_statistics->toString());
  nighthawk::client::Output output;
  output.set_allocated_options(options_->toCommandLineOptions().release());

  struct timeval tv;
  gettimeofday(&tv, NULL);
  output.mutable_timestamp()->set_seconds(tv.tv_sec);
  output.mutable_timestamp()->set_nanos(tv.tv_usec * 1000);
  merged_statistics->toProto(output);

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
  return true;
}

} // namespace Client
} // namespace Nighthawk

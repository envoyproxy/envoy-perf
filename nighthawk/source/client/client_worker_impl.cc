#include "nighthawk/source/client/client_worker_impl.h"

#include "nighthawk/source/common/platform_util_impl.h"

namespace Nighthawk {
namespace Client {

ClientWorkerImpl::ClientWorkerImpl(Envoy::Api::Api& api, Envoy::ThreadLocal::Instance& tls,
                                   const BenchmarkClientFactory& benchmark_client_factory,
                                   const SequencerFactory& sequencer_factory, const Uri uri,
                                   Envoy::Stats::StorePtr&& store, const int worker_number,
                                   const Envoy::MonotonicTime starting_time)
    : WorkerImpl(api, tls, std::move(store)), uri_(uri), worker_number_(worker_number),
      starting_time_(starting_time),
      benchmark_client_(benchmark_client_factory.create(api, *dispatcher_, *store_, uri)),
      sequencer_(sequencer_factory.create(time_source_, *dispatcher_, *benchmark_client_)) {}

void ClientWorkerImpl::simpleWarmup() {
  ENVOY_LOG(debug, "> worker {}: warming up.", worker_number_);
  // TODO(oschaaf): Maybe add BenchmarkClient::warmup() and call that here.
  // Ideally that would warm up the pool better, by prefetching the requested amount of
  // connections. Currently it is possible to use less connections then specified if
  // completions are fast enough. While this may be an assert, it may also be annoying
  // when comparing results to some other tools, which do open up the specified amount
  // of connections.
  benchmark_client_->tryStartOne([this] { dispatcher_->exit(); });
  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);
}

void ClientWorkerImpl::delayStart() {
  PlatformUtilImpl platform_util;
  // TODO(oschaaf): We could use dispatcher to sleep, but currently it has a 1 ms resolution
  // which is rather coarse for our purpose here.
  ENVOY_LOG(debug, "> worker {}: waiting", worker_number_);
  int count = 0;
  while (time_source_.monotonicTime() < starting_time_) {
    count++;
    platform_util.yieldCurrentThread();
  }
  if (count == 0) {
    ENVOY_LOG(warn,
              "> worker {} arrived late and did not have to spin/wait for its turn to start.");
  }
  ENVOY_LOG(debug, "> worker {}: started", worker_number_);
}

void ClientWorkerImpl::work() {
  benchmark_client_->initialize(*Envoy::Runtime::LoaderSingleton::getExisting());
  simpleWarmup();
  benchmark_client_->setMeasureLatencies(true);
  delayStart();
  sequencer_->start();
  sequencer_->waitForCompletion();
  benchmark_client_->terminate();
  success_ = true;
  dispatcher_->exit();
}

StatisticPtrMap ClientWorkerImpl::statistics() const {
  StatisticPtrMap statistics;
  StatisticPtrMap s1 = benchmark_client_->statistics();
  StatisticPtrMap s2 = sequencer_->statistics();
  statistics.insert(s1.begin(), s1.end());
  statistics.insert(s2.begin(), s2.end());
  return statistics;
}

} // namespace Client
} // namespace Nighthawk
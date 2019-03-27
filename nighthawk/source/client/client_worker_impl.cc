#include "nighthawk/source/client/client_worker_impl.h"

namespace Nighthawk {
namespace Client {

// TODO(oschaaf): const the stuff
ClientWorkerImpl::ClientWorkerImpl(Envoy::Api::Api& api, Envoy::ThreadLocal::Instance& tls,
                                   const BenchmarkClientFactory& benchmark_client_factory,
                                   const SequencerFactory& sequencer_factory, const Uri uri,
                                   Envoy::Stats::StorePtr&& store, int worker_number,
                                   uint64_t start_delay_usec)
    : WorkerImpl(api, tls, std::move(store)), uri_(uri), worker_number_(worker_number),
      start_delay_usec_(start_delay_usec) {
  benchmark_client_ = benchmark_client_factory.create(api, *dispatcher_, *store_, uri);
  sequencer_ = sequencer_factory.create(time_source_, *dispatcher_, *benchmark_client_);
}

void ClientWorkerImpl::simpleWarmup() {
  ENVOY_LOG(debug, "> worker {}: warming up.", worker_number_);
  // TODO(oschaaf): Maybe add BenchmarkClient::warmup() and call that here.
  // Idealy that would warm up the pool better, by prefetching the requested amount of
  // connections. Currently it is possible to use less connections then specified if
  // completions are fast enough. While this may be an assert, it may also be annoying
  // when comparing results to some other tools, which do open up the specified amount
  // of connections.
  benchmark_client_->tryStartOne([this] { dispatcher_->exit(); });
  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);
}

void ClientWorkerImpl::delayStart() {
  ENVOY_LOG(debug, "> worker {}: Delay start of worker for {} us.", worker_number_,
            start_delay_usec_);
  // TODO(oschaaf): We could use dispatcher to sleep, but currently it has a 1 ms resolution
  // which is rather coarse for our purpose here.
  // TODO(oschaaf): Instead of usleep, it would perhaps be better to provide an absolute
  // starting time to wait for in a (spin loop of the) sequencer implementation for high
  // accuracy when releasing the initial requests.
  usleep(start_delay_usec_);
}

void ClientWorkerImpl::work() {
  // We need the dispatcher to run here to avoid a runtime assert triggering.
  // This is effectively a no-op.
  // TODO(oschaaf):
  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);
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
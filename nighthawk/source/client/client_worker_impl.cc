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
  // Ideally we prefetch the requested amount of connections.
  // Currently it is possible to use less connections then specified if
  // completions are fast enough. While this may be an asset, it may also be annoying
  // when comparing results to some other tools, which do open up the specified amount
  // of connections.
  benchmark_client_->tryStartOne([this] { dispatcher_->exit(); });
  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);
}

void ClientWorkerImpl::delayStart() {
  PlatformUtilImpl platform_util;

  // The spin loop we perform serves two purposes:
  // 1. It warms up the hardware, hopefully steadying CPU clock frequency before we begin.
  // 2. We can be highly accurate with respect to the designated start time.
  // The latter is useful, because this attribute may be used to distribute worker starts evenly in
  // time with respect to the global frequency. An example: Let's assume we have two workers w0/w1,
  // which should maintain a combined global pace of 1000Hz. w0 and w1 both run at 500Hz, but
  // ideally their execution is evenly spaced in time, and not overlapping. Workers start offsets
  // can be computed like "worker_number*(1/global_frequency))", which would yield T0+[0ms, 1ms].
  // This helps reduce batching/queueing effects, both initially, but also by calibrating the linear
  // rate limiter we currently have to a precise starting time, which helps later on.
  // TODO(oschaaf): Arguably, this ought to be the job of a rate limiter with awareness of the
  // global status quo, which we do not have right now. This has been noted in the track-for-future
  // issue.
  // TODO(oschaaf): I retrospect, this probably could be implemented by directly assigning a
  // starting time to the rate limiter. This would make generalizing our strategies, as
  // the sequencer would be responsible for how we wait (e.g. dispatcher.sleep or spinning), and the
  // rate limiter should be in full control of what requests get released when.
  // Then this step could still exist in some form, but with the sole purpose of warming up the
  // hardware.
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
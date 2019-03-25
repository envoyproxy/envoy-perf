#include "nighthawk/source/client/client_worker_impl.h"

namespace Nighthawk {
namespace Client {

// TODO(oschaaf): const the stuff
ClientWorkerImpl::ClientWorkerImpl(OptionInterpreter& option_interpreter, Envoy::Api::Api& api,
                                   Envoy::ThreadLocal::Instance& tls, const Uri uri,
                                   Envoy::Stats::StorePtr&& store, int worker_number,
                                   uint64_t start_delay_usec)
    : WorkerImpl(api, tls, std::move(store)), uri_(uri), worker_number_(worker_number),
      start_delay_usec_(start_delay_usec) {
  benchmark_client_ = option_interpreter.createBenchmarkClient(api, *dispatcher_, uri);
  sequencer_ = option_interpreter.createSequencer(time_source_, *dispatcher_, *benchmark_client_);
}

void ClientWorkerImpl::logResult() {
  std::string worker_percentiles = "{}\n{}";

  for (auto statistic : benchmark_client_->statistics()) {
    worker_percentiles =
        fmt::format(worker_percentiles, statistic.first, statistic.second->toString() + "\n{}\n{}");
  }
  for (auto statistic : sequencer_->statistics()) {
    worker_percentiles =
        fmt::format(worker_percentiles, statistic.first, statistic.second->toString() + "\n{}\n{}");
  }

  worker_percentiles = fmt::format(worker_percentiles, "", "");

  CounterFilter filter = [](std::string, uint64_t value) { return value > 0; };
  // TODO(oschaaf): output the counters.
  // ENVOY_LOG(info, "> worker {}\n{}\n{}", worker_number_,
  //          benchmark_client_->countersToString(filter), worker_percentiles);
}

void ClientWorkerImpl::simpleWarmup() {
  ENVOY_LOG(debug, "> worker {}: warming up.", worker_number_);
  benchmark_client_->tryStartOne([this] { dispatcher_->exit(); });
  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);
}

void ClientWorkerImpl::delayStart() {
  ENVOY_LOG(debug, "> worker {}: Delay start of worker for {} us.", worker_number_,
            start_delay_usec_);
  // TODO(oschaaf): We could use dispatcher to sleep, but currently it has a 1 ms resolution
  // which is rather coarse for our purpose here.
  // TODO(oschaaf): Instead of usleep, it would probably be better to provide an absolute
  // starting time and wait for that in the (spin loop of the) sequencer implementation for high
  // accuracy.
  usleep(start_delay_usec_);
}

void ClientWorkerImpl::work() {
  try {
    benchmark_client_->initialize(*Envoy::Runtime::LoaderSingleton::getExisting());
  } catch (const UriException) {
    success_ = false;
    return;
  }

  simpleWarmup();
  benchmark_client_->setMeasureLatencies(true);
  delayStart();
  sequencer_->start();
  sequencer_->waitForCompletion();
  logResult();
  benchmark_client_->terminate();
  success_ = true;
  dispatcher_->exit();
}

StatisticPtrMap ClientWorkerImpl::statistics() const {
  StatisticPtrMap statistics(benchmark_client_->statistics());

  // TODO(oschaaf): should check for duplicate id's and except.
  for (auto stat : sequencer_->statistics()) {
    statistics[stat.first] = stat.second;
  }

  return statistics;
}

} // namespace Client
} // namespace Nighthawk
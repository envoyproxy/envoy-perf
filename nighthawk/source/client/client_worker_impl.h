#pragma once

#include "envoy/api/api.h"

#include "nighthawk/client/benchmark_client.h"
#include "nighthawk/client/client_worker.h"
#include "nighthawk/client/option_interpreter.h"
#include "nighthawk/common/sequencer.h"

#include "nighthawk/source/common/worker_impl.h"

namespace Nighthawk {
namespace Client {

class ClientWorkerImpl : public WorkerImpl,
                         virtual public ClientWorker,
                         Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  ClientWorkerImpl(OptionInterpreter& option_interpreter, Envoy::Api::Api& api,
                   Envoy::ThreadLocal::Instance& tls, Envoy::Stats::StorePtr&& store,
                   int worker_number, uint64_t start_delay_usec);

  StatisticPtrMap statistics() const override;

protected:
  void work() override;

private:
  void simpleWarmup();
  void delayStart();
  void logResult();

  std::unique_ptr<BenchmarkClient> benchmark_client_;
  std::unique_ptr<Sequencer> sequencer_;
  const int worker_number_;
  const uint64_t start_delay_usec_;
};

typedef std::unique_ptr<ClientWorkerImpl> ClientWorkerImplPtr;

} // namespace Client
} // namespace Nighthawk
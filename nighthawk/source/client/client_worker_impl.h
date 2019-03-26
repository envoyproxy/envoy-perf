#pragma once

#include "envoy/api/api.h"

#include "nighthawk/client/benchmark_client.h"
#include "nighthawk/client/client_worker.h"
#include "nighthawk/client/factories.h"
#include "nighthawk/common/sequencer.h"

#include "nighthawk/source/common/utility.h"
#include "nighthawk/source/common/worker_impl.h"

namespace Nighthawk {
namespace Client {

class ClientWorkerImpl : public WorkerImpl,
                         virtual public ClientWorker,
                         Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  ClientWorkerImpl(Envoy::Api::Api& api, Envoy::ThreadLocal::Instance& tls,
                   const BenchmarkClientFactory& benchmark_client_factory,
                   const SequencerFactory& sequencer_factory, const Uri uri,
                   Envoy::Stats::StorePtr&& store, int worker_number, uint64_t start_delay_usec);

  StatisticPtrMap statistics() const override;

  const BenchmarkClient& benchmark_client() const override { return *benchmark_client_; }
  bool success() const override { return success_; }

protected:
  void work() override;

private:
  void simpleWarmup();
  void delayStart();
  std::unique_ptr<BenchmarkClient> benchmark_client_;
  std::unique_ptr<Sequencer> sequencer_;
  const Uri uri_;
  const int worker_number_;
  const uint64_t start_delay_usec_;
  bool success_{};
};

typedef std::unique_ptr<ClientWorkerImpl> ClientWorkerImplPtr;

} // namespace Client
} // namespace Nighthawk
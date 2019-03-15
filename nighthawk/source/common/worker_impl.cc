#include "nighthawk/source/common/worker_impl.h"

#include "common/runtime/runtime_impl.h"
#include "envoy/thread_local/thread_local.h"

using namespace std::chrono_literals;

namespace Nighthawk {

WorkerImpl::WorkerImpl(Envoy::Api::Api& api, Envoy::ThreadLocal::Instance& tls,
                       Envoy::Stats::StorePtr&& store)
    : thread_factory_(api.threadFactory()), dispatcher_(api.allocateDispatcher()), tls_(tls),
      store_(std::move(store)), generator_(std::make_unique<Envoy::Runtime::RandomGeneratorImpl>()),
      time_source_(api.timeSource()), started_(false), completed_(false) {
  tls.registerThread(*dispatcher_, false);
  runtime_ = std::make_unique<Envoy::Runtime::LoaderImpl>(*generator_, *store_, tls);
}

WorkerImpl::~WorkerImpl() { tls_.shutdownThread(); }

void WorkerImpl::start() {
  ASSERT(!started_ && !completed_);
  started_ = true;
  thread_ = thread_factory_.createThread([this]() { work(); });
}

void WorkerImpl::waitForCompletion() {
  ASSERT(started_ && !completed_);
  completed_ = true;
  thread_->join();
}

} // namespace Nighthawk
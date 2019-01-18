#pragma once

#include "common/common/logger.h"

#include "envoy/event/timer.h"
#include "envoy/network/address.h"
#include "envoy/stats/store.h"

#include "nighthawk/client/options.h"
#include "nighthawk/client/worker.h"

namespace Nighthawk {
namespace Client {

class Main : public Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  Main(int argc, const char* const* argv);
  Main(Client::OptionsPtr&& options);
  ~Main();

  bool run();

private:
  OptionsPtr options_;
  std::unique_ptr<Envoy::Event::TimeSystem> time_system_;
  std::unique_ptr<Envoy::Logger::Context> logging_context_;
  Envoy::Network::Address::InstanceConstSharedPtr target_address_;
  WorkerPtr worker_;
  void configureComponentLogLevels(spdlog::level::level_enum level);
};

} // namespace Client
} // namespace Nighthawk

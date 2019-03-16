#pragma once

#include "common/common/logger.h"

#include "envoy/network/address.h"
#include "envoy/stats/store.h"

#include "nighthawk/client/client_worker.h"
#include "nighthawk/client/option_interpreter.h"
#include "nighthawk/client/options.h"
#include "nighthawk/common/statistic.h"

namespace Nighthawk {
namespace Client {

class Main : public Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  Main(int argc, const char* const* argv);
  Main(Client::OptionsPtr&& options);
  ~Main();
  bool run();

private:
  uint32_t determineConcurrency() const;
  void configureComponentLogLevels(spdlog::level::level_enum level);
  bool runWorkers(OptionInterpreter& option_interpreter,
                  std::vector<StatisticPtr>& merged_statistics) const;
  std::vector<StatisticPtr>
  mergeWorkerStatistics(const OptionInterpreter& option_interpreter,
                        const std::vector<ClientWorkerPtr>& workers) const;
  void outputCliStats(const std::vector<StatisticPtr>& merged_statistics) const;

  OptionsPtr options_;
  std::unique_ptr<Envoy::Logger::Context> logging_context_;
};

} // namespace Client
} // namespace Nighthawk

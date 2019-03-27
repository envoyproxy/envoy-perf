#pragma once

#include "nighthawk/client/output_formatter.h"

#include <cstdint>

namespace Nighthawk {
namespace Client {

class OutputFormatterImpl : public OutputFormatter {
public:
  OutputFormatterImpl(const Options& options, const std::vector<StatisticPtr>& merged_statistics,
                      const std::map<std::string, uint64_t>& merged_counters);

  void writeToFile(std::string path) const override;

protected:
  const Options& options_;
  const std::vector<StatisticPtr>& merged_statistics_;
  const std::map<std::string, uint64_t>& merged_counters_;
};

class ConsoleOutputFormatterImpl : public OutputFormatterImpl {
public:
  ConsoleOutputFormatterImpl(const Options& options,
                             const std::vector<StatisticPtr>& merged_statistics,
                             const std::map<std::string, uint64_t>& merged_counters);
  std::string toString() const override;
};

class JsonOutputFormatterImpl : public OutputFormatterImpl {
public:
  JsonOutputFormatterImpl(const Options& options,
                          const std::vector<StatisticPtr>& merged_statistics,
                          const std::map<std::string, uint64_t>& merged_counters);
  std::string toString() const override;
};

} // namespace Client
} // namespace Nighthawk
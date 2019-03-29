#pragma once

#include "nighthawk/client/output_formatter.h"

#include "envoy/common/time.h"

#include "common/protobuf/protobuf.h"

#include <cstdint>

namespace Nighthawk {
namespace Client {

class OutputFormatterImpl : public OutputFormatter {
public:
  /**
   * @param time_source Time source that will be used to generate a timestamp in the output.
   * @param options The options that led up to the output that will be computed by this instance.
   * @param merged_statistics Vector of statistic instances which represent the global results
   * (after merging results if multiple workers are involved).
   * @param merged_counters Map of counters, keyed by id, representing the global result (after
   * summing up the counters if multiple workers are involved).
   */
  OutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options,
                      const std::vector<StatisticPtr>& merged_statistics,
                      const std::map<std::string, uint64_t>& merged_counters);

protected:
  Envoy::ProtobufTypes::MessagePtr toProto() const;

  Envoy::TimeSource& time_source_;
  const Options& options_;
  const std::vector<StatisticPtr>& merged_statistics_;
  const std::map<std::string, uint64_t>& merged_counters_;
};

class ConsoleOutputFormatterImpl : public OutputFormatterImpl {
public:
  ConsoleOutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options,
                             const std::vector<StatisticPtr>& merged_statistics,
                             const std::map<std::string, uint64_t>& merged_counters);
  std::string toString() const override;
};

class JsonOutputFormatterImpl : public OutputFormatterImpl {
public:
  JsonOutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options,
                          const std::vector<StatisticPtr>& merged_statistics,
                          const std::map<std::string, uint64_t>& merged_counters);
  std::string toString() const override;
};

class YamlOutputFormatterImpl : public OutputFormatterImpl {
public:
  YamlOutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options,
                          const std::vector<StatisticPtr>& merged_statistics,
                          const std::map<std::string, uint64_t>& merged_counters);
  std::string toString() const override;
};

} // namespace Client
} // namespace Nighthawk
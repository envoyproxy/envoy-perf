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
  OutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options);
  OutputFormatterImpl(const OutputFormatter& formatter);

  void addResult(const std::string name, const std::vector<StatisticPtr>& statistics,
                 const std::map<std::string, uint64_t>& counters) override;

  nighthawk::client::Output toProto() const override;

private:
  nighthawk::client::Output output_;
};

class ConsoleOutputFormatterImpl : public OutputFormatterImpl {
public:
  ConsoleOutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options);
  ConsoleOutputFormatterImpl(const OutputFormatter& formatter);

  std::string toString() const override;
};

class JsonOutputFormatterImpl : public OutputFormatterImpl {
public:
  JsonOutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options);
  JsonOutputFormatterImpl(const OutputFormatter& formatter);
  std::string toString() const override;
};

class YamlOutputFormatterImpl : public OutputFormatterImpl {
public:
  YamlOutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options);
  YamlOutputFormatterImpl(const OutputFormatter& formatter);
  std::string toString() const override;
};

} // namespace Client
} // namespace Nighthawk
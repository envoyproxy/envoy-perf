#pragma once

#include "nighthawk/client/output_formatter.h"

#include "envoy/common/time.h"

#include "common/protobuf/protobuf.h"

#include <cstdint>

namespace Nighthawk {
namespace Client {

class OutputFormatterImpl : public OutputFormatter {
public:
  OutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options,
                      const std::vector<StatisticPtr>& merged_statistics,
                      const std::map<std::string, uint64_t>& merged_counters);

  Envoy::ProtobufTypes::MessagePtr toProto() const;

protected:
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
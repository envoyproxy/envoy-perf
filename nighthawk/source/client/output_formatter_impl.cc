#include "nighthawk/source/client/output_formatter_impl.h"

#include <chrono>
#include <sstream>

#include "common/protobuf/utility.h"

namespace Nighthawk {
namespace Client {

OutputFormatterImpl::OutputFormatterImpl(Envoy::TimeSource& time_source, const Options& options,
                                         const std::vector<StatisticPtr>& merged_statistics,
                                         const std::map<std::string, uint64_t>& merged_counters)
    : time_source_(time_source), options_(options), merged_statistics_(merged_statistics),
      merged_counters_(merged_counters) {}

ConsoleOutputFormatterImpl::ConsoleOutputFormatterImpl(
    Envoy::TimeSource& time_source, const Options& options,
    const std::vector<StatisticPtr>& merged_statistics,
    const std::map<std::string, uint64_t>& merged_counters)
    : OutputFormatterImpl(time_source, options, merged_statistics, merged_counters) {}

std::string ConsoleOutputFormatterImpl::toString() const {
  std::stringstream s;

  // TODO(oschaaf): echo non-default options to CLI output?
  s << "Merged statistics:\n";
  for (auto& statistic : merged_statistics_) {
    if (statistic->count() > 0) {
      s << fmt::format("{}: {}\n", statistic->id(), statistic->toString(), "\n");
    }
  }
  s << "\nMerged counters\n";
  for (auto counter : merged_counters_) {
    s << fmt::format("counter {}:{}\n", counter.first, counter.second);
  }
  return s.str();
}

Envoy::ProtobufTypes::MessagePtr OutputFormatterImpl::toProto() const {
  nighthawk::client::Output output;
  output.set_allocated_options(options_.toCommandLineOptions().release());

  auto ts = time_source_.systemTime().time_since_epoch();
  auto seconds = std::chrono::duration_cast<std::chrono::seconds>(ts);
  output.mutable_timestamp()->set_seconds(seconds.count());
  output.mutable_timestamp()->set_nanos(
      std::chrono::duration_cast<std::chrono::nanoseconds>(ts - seconds).count());

  auto result = output.add_results();
  result->set_name("global");
  for (auto& statistic : merged_statistics_) {
    *(result->add_statistics()) = statistic->toProto();
  }
  for (auto counter : merged_counters_) {
    auto counters = result->add_counters();
    counters->set_name(counter.first);
    counters->set_value(counter.second);
  }
  return std::make_unique<nighthawk::client::Output>(std::move(output));
}

JsonOutputFormatterImpl::JsonOutputFormatterImpl(
    Envoy::TimeSource& time_source, const Options& options,
    const std::vector<StatisticPtr>& merged_statistics,
    const std::map<std::string, uint64_t>& merged_counters)
    : OutputFormatterImpl(time_source, options, merged_statistics, merged_counters) {}

std::string JsonOutputFormatterImpl::toString() const {
  auto output = toProto();
  return Envoy::MessageUtil::getJsonStringFromMessage(*output, true, true);
}

YamlOutputFormatterImpl::YamlOutputFormatterImpl(
    Envoy::TimeSource& time_source, const Options& options,
    const std::vector<StatisticPtr>& merged_statistics,
    const std::map<std::string, uint64_t>& merged_counters)
    : OutputFormatterImpl(time_source, options, merged_statistics, merged_counters) {}

std::string YamlOutputFormatterImpl::toString() const {
  auto output = toProto();
  return Envoy::MessageUtil::getYamlStringFromMessage(*output, true, true);
}

} // namespace Client
} // namespace Nighthawk
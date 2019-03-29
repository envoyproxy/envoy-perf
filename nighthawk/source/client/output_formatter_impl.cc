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
      s << fmt::format("{}: {}\n", statistic->id(), statistic->toString());
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
  *(output.mutable_timestamp()) = google::protobuf::util::TimeUtil::NanosecondsToTimestamp(
      time_source_.systemTime().time_since_epoch().count());
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
  return Envoy::MessageUtil::getJsonStringFromMessage(*toProto(), true, true);
}

YamlOutputFormatterImpl::YamlOutputFormatterImpl(
    Envoy::TimeSource& time_source, const Options& options,
    const std::vector<StatisticPtr>& merged_statistics,
    const std::map<std::string, uint64_t>& merged_counters)
    : OutputFormatterImpl(time_source, options, merged_statistics, merged_counters) {}

std::string YamlOutputFormatterImpl::toString() const {
  return Envoy::MessageUtil::getYamlStringFromMessage(*toProto(), true, true);
}

} // namespace Client
} // namespace Nighthawk
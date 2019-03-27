#include "nighthawk/source/client/output_formatter_impl.h"

#include <sstream>

#include <google/protobuf/util/json_util.h>

namespace Nighthawk {
namespace Client {

OutputFormatterImpl::OutputFormatterImpl(const Options& options,
                                         const std::vector<StatisticPtr>& merged_statistics,
                                         const std::map<std::string, uint64_t>& merged_counters)
    : options_(options), merged_statistics_(merged_statistics), merged_counters_(merged_counters) {}

ConsoleOutputFormatterImpl::ConsoleOutputFormatterImpl(
    const Options& options, const std::vector<StatisticPtr>& merged_statistics,
    const std::map<std::string, uint64_t>& merged_counters)
    : OutputFormatterImpl(options, merged_statistics, merged_counters) {}

void OutputFormatterImpl::writeToFile(std::string) const { std::string output = toString(); }

std::string ConsoleOutputFormatterImpl::toString() const {
  std::stringstream s;

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

JsonOutputFormatterImpl::JsonOutputFormatterImpl(
    const Options& options, const std::vector<StatisticPtr>& merged_statistics,
    const std::map<std::string, uint64_t>& merged_counters)
    : OutputFormatterImpl(options, merged_statistics, merged_counters) {}

std::string JsonOutputFormatterImpl::toString() const {
  nighthawk::client::Output output;
  output.set_allocated_options(options_.toCommandLineOptions().release());

  struct timeval tv;
  gettimeofday(&tv, NULL);
  output.mutable_timestamp()->set_seconds(tv.tv_sec);
  output.mutable_timestamp()->set_nanos(tv.tv_usec * 1000);

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

  std::string str;
  google::protobuf::util::JsonPrintOptions options;
  google::protobuf::util::MessageToJsonString(output, &str, options);
  return str;
}

} // namespace Client
} // namespace Nighthawk
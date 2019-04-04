#include <chrono>

#include "gtest/gtest.h"

#include "nighthawk/source/client/output_formatter_impl.h"

#include "test/test_common/simulated_time_system.h"

#include "common/filesystem/filesystem_impl.h"

#include "nighthawk/source/client/options.pb.h"
#include "nighthawk/source/common/statistic_impl.h"
#include "nighthawk/test/mocks.h"
#include "nighthawk/test/test_common/environment.h"

using namespace std::chrono_literals;
using namespace testing;

namespace Nighthawk {
namespace Client {

class OutputFormatterTest : public Test {
public:
  OutputFormatterTest() {
    StatisticPtr used_statistic = std::make_unique<StreamingStatistic>();
    StatisticPtr empty_statistic = std::make_unique<StreamingStatistic>();
    used_statistic->setId("stat_id");
    used_statistic->addValue(1000000);
    used_statistic->addValue(2000000);
    used_statistic->addValue(3000000);
    statistics_.push_back(std::move(used_statistic));
    statistics_.push_back(std::move(empty_statistic));
    counters_["foo"] = 1;
    counters_["bar"] = 2;
    time_system_.setSystemTime(std::chrono::milliseconds(1234567891567));
  }

  Envoy::Event::SimulatedTimeSystem time_system_;
  Envoy::Filesystem::InstanceImplPosix filesystem_;
  MockOptions options_;
  std::vector<StatisticPtr> statistics_;
  std::map<std::string, uint64_t> counters_;
};

TEST_F(OutputFormatterTest, CliFormatter) {
  ConsoleOutputFormatterImpl formatter(time_system_, options_);
  formatter.addResult("global", statistics_, counters_);
  EXPECT_EQ(filesystem_.fileReadToEnd(TestEnvironment::runfilesPath(
                "nighthawk/test/test_data/output_formatter.txt.gold")),
            formatter.toString());
}

TEST_F(OutputFormatterTest, JsonFormatter) {
  JsonOutputFormatterImpl formatter(time_system_, options_);
  formatter.addResult("global", statistics_, counters_);
  EXPECT_CALL(options_, toCommandLineOptions)
      .WillOnce(Return(ByMove(std::make_unique<nighthawk::client::CommandLineOptions>())));
  EXPECT_EQ(filesystem_.fileReadToEnd(TestEnvironment::runfilesPath(
                "nighthawk/test/test_data/output_formatter.json.gold")),
            formatter.toString());
}

TEST_F(OutputFormatterTest, YamlFormatter) {
  YamlOutputFormatterImpl formatter(time_system_, options_);
  formatter.addResult("global", statistics_, counters_);
  EXPECT_CALL(options_, toCommandLineOptions)
      .WillOnce(Return(ByMove(std::make_unique<nighthawk::client::CommandLineOptions>())));
  EXPECT_EQ(filesystem_.fileReadToEnd(TestEnvironment::runfilesPath(
                "nighthawk/test/test_data/output_formatter.yaml.gold")),
            formatter.toString());
}

} // namespace Client
} // namespace Nighthawk

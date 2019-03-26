#include <chrono>

#include "gtest/gtest.h"

#include "test/mocks/event/mocks.h"
#include "test/mocks/stats/mocks.h"

#include "test/test_common/utility.h"

#include "common/api/api_impl.h"

#include "nighthawk/test/mocks.h"

#include "nighthawk/source/client/option_interpreter_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {
namespace Client {

class OptionsInterpreterTest : public testing::Test {
public:
  OptionsInterpreterTest() : api_(Envoy::Api::createApiForTest(stats_store_)) {}

  Envoy::Api::ApiPtr api_;
  Envoy::Stats::MockIsolatedStatsStore stats_store_;
  Envoy::Event::MockDispatcher dispatcher_;
  MockOptions options_;
};

TEST_F(OptionsInterpreterTest, createBenchmarkClient) {
  OptionInterpreterImpl interpreter(options_);

  EXPECT_CALL(options_, timeout()).Times(1);
  EXPECT_CALL(options_, connections()).Times(1);
  EXPECT_CALL(options_, h2()).Times(1);

  auto benchmark_client = interpreter.createBenchmarkClient(*api_, dispatcher_, stats_store_,
                                                            Uri::Parse("http://foo/"));
}

TEST_F(OptionsInterpreterTest, createSequencer) {
  OptionInterpreterImpl interpreter(options_);
  MockBenchmarkClient benchmark_client;

  EXPECT_CALL(options_, timeout()).Times(1);
  EXPECT_CALL(options_, duration()).Times(1).WillOnce(testing::Return(1s));
  EXPECT_CALL(options_, requests_per_second()).Times(1).WillOnce(testing::Return(1));

  EXPECT_CALL(dispatcher_, createTimer_(_)).Times(2);

  auto sequencer = interpreter.createSequencer(api_->timeSource(), dispatcher_, benchmark_client);
}

TEST_F(OptionsInterpreterTest, simpleInstantiations) {
  OptionInterpreterImpl interpreter(options_);
  interpreter.createStatsStore();
  interpreter.createStatistic();
  interpreter.getPlatformUtil();
}

} // namespace Client
} // namespace Nighthawk

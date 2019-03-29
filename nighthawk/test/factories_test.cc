#include <chrono>

#include "gtest/gtest.h"

#include "test/mocks/event/mocks.h"
#include "test/mocks/stats/mocks.h"

#include "test/test_common/utility.h"

#include "common/api/api_impl.h"

#include "nighthawk/test/mocks.h"

#include "nighthawk/source/client/factories_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {
namespace Client {

class FactoriesTest : public testing::Test {
public:
  FactoriesTest() : api_(Envoy::Api::createApiForTest(stats_store_)) {}

  Envoy::Api::ApiPtr api_;
  Envoy::Stats::MockIsolatedStatsStore stats_store_;
  Envoy::Event::MockDispatcher dispatcher_;
  MockOptions options_;
};

TEST_F(FactoriesTest, CreateBenchmarkClient) {
  BenchmarkClientFactoryImpl factory(options_);

  EXPECT_CALL(options_, timeout()).Times(1);
  EXPECT_CALL(options_, connections()).Times(1);
  EXPECT_CALL(options_, h2()).Times(1);

  auto benchmark_client =
      factory.create(*api_, dispatcher_, stats_store_, Uri::Parse("http://foo/"));
  EXPECT_NE(nullptr, benchmark_client.get());
}

TEST_F(FactoriesTest, CreateSequencer) {
  SequencerFactoryImpl factory(options_);
  MockBenchmarkClient benchmark_client;

  EXPECT_CALL(options_, timeout()).Times(1);
  EXPECT_CALL(options_, duration()).Times(1).WillOnce(testing::Return(1s));
  EXPECT_CALL(options_, requests_per_second()).Times(1).WillOnce(testing::Return(1));
  EXPECT_CALL(dispatcher_, createTimer_(_)).Times(2);

  auto sequencer = factory.create(api_->timeSource(), dispatcher_, benchmark_client);
  EXPECT_NE(nullptr, sequencer.get());
}

TEST_F(FactoriesTest, CreateStore) {
  StoreFactoryImpl factory(options_);
  EXPECT_NE(nullptr, factory.create().get());
}

TEST_F(FactoriesTest, CreateStatistic) {
  StatisticFactoryImpl factory(options_);
  EXPECT_NE(nullptr, factory.create().get());
}

} // namespace Client
} // namespace Nighthawk

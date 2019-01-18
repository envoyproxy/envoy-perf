#include <chrono>

#include "gtest/gtest.h"

#include "test/test_common/simulated_time_system.h"

#include "nighthawk/common/exception.h"

#include "common/streaming_stats.h"

using namespace std::chrono_literals;

namespace Nighthawk {

class StreamingStatsTest : public testing::Test {};

TEST_F(StreamingStatsTest, BasicTest) {
  StreamingStats a;
  StreamingStats b;

  std::vector<int> a_values{1, 2, 3};
  std::vector<int> b_values{1234, 6543456, 342335};

  for (int value : a_values) {
    a.addValue(value);
  }
  for (int value : b_values) {
    b.addValue(value);
  }

  // simple case
  EXPECT_EQ(3, a.count());
  EXPECT_EQ(2, a.mean());
  EXPECT_EQ(1, a.variance());
  EXPECT_EQ(1, a.stdev());

  // some more exciting numbers
  EXPECT_EQ(3, b.count());
  EXPECT_EQ(2295675, b.mean());
  EXPECT_EQ(13561820041021, b.variance());
  EXPECT_DOUBLE_EQ(3682637.6472605884, b.stdev());

  StreamingStats c = a.combine(b);
  // test the numbers look like what we expect after combing.
  EXPECT_EQ(6, c.count());
  EXPECT_DOUBLE_EQ(1147838.5, c.mean());
  EXPECT_EQ(7005762373287.5, c.variance());
  EXPECT_DOUBLE_EQ(2646840.0732359141, c.stdev());
}

} // namespace Nighthawk

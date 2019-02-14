#include "nighthawk/source/common/statistic_impl.h"

#include "nighthawk/common/statistic.h"

#include "gtest/gtest.h"

namespace Nighthawk {

using MyTypes = ::testing::Types<InMemoryStatistic, HdrStatistic, StreamingStatistic>;

template <typename T> class StatisticTest : public testing::Test {};

class Helper {
public:
  /**
   * With 0 significant digits passed, this uses EXPECT_DOUBLE_EQ. Otherwise EXPECT_NEAR
   * will be called with a computed acceptable range based on the number of significant
   * digits and tested_value.
   * @param expected_value the expected value
   * @param tested_value the tested_value
   * @param significant the number of significant digits that should be used to compare values.
   */
  static void expect_near(double expected_value, double tested_value, uint64_t significant) {
    if (significant > 0) {
      EXPECT_NEAR(expected_value, tested_value,
                  std::pow(10, std::ceil(std::log10(tested_value)) - 1 - significant));
    } else {
      EXPECT_DOUBLE_EQ(expected_value, tested_value);
    }
  }

private:
  Helper() = default;
};

TYPED_TEST_SUITE(StatisticTest, MyTypes);

TYPED_TEST(StatisticTest, Simple) {
  TypeParam a;
  TypeParam b;

  std::vector<int> a_values{1, 2, 3};
  std::vector<int> b_values{1234, 6543456, 342335};

  for (int value : a_values) {
    a.addValue(value);
  }
  EXPECT_EQ(3, a.count());

  for (int value : b_values) {
    b.addValue(value);
  }
  EXPECT_EQ(3, b.count());

  Helper::expect_near(2, a.mean(), a.significant_digits());
  Helper::expect_near(1, a.variance(), a.significant_digits());
  Helper::expect_near(1, a.stdev(), a.significant_digits());

  Helper::expect_near(2295675, b.mean(), a.significant_digits());
  Helper::expect_near(13561820041021, b.variance(), a.significant_digits());
  Helper::expect_near(3682637.6472605884, b.stdev(), a.significant_digits());

  auto c = a.combine(b);
  EXPECT_EQ(6, c->count());
  Helper::expect_near(1147838.5, c->mean(), c->significant_digits());
  Helper::expect_near(7005762373287.5, c->variance(), c->significant_digits());
  Helper::expect_near(2646840.0732359141, c->stdev(), c->significant_digits());
}

// TODO(oschaaf): This needs tests for the proto output updates.

} // namespace Nighthawk

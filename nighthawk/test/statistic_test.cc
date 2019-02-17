#include <typeinfo> // std::bad_cast

#include "gtest/gtest.h"

#include "nighthawk/common/statistic.h"
#include "nighthawk/source/common/statistic_impl.h"

namespace Nighthawk {

using MyTypes = ::testing::Types<InMemoryStatistic, HdrStatistic, StreamingStatistic>;

template <typename T> class TypedStatisticTest : public testing::Test {};

class Helper {
public:
  /**
   * With 0 significant digits passed, this uses EXPECT_DOUBLE_EQ. Otherwise expectNear
   * will be called with a computed acceptable range based on the number of significant
   * digits and tested_value.
   * @param expected_value the expected value
   * @param tested_value the tested_value
   * @param significant the number of significant digits that should be used to compare values.
   */
  static void expectNear(double expected_value, double tested_value, uint64_t significant) {
    if (significant > 0) {
      EXPECT_NEAR(expected_value, tested_value,
                  std::pow(10, std::ceil(std::log10(tested_value)) - 1 - significant));
    } else {
      EXPECT_DOUBLE_EQ(expected_value, tested_value);
    }
  }
};

TYPED_TEST_SUITE(TypedStatisticTest, MyTypes);

TYPED_TEST(TypedStatisticTest, Simple) {
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

  Helper::expectNear(2.0, a.mean(), a.significantDigits());
  Helper::expectNear(0.6666666666666666, a.pvariance(), a.significantDigits());
  Helper::expectNear(0.816496580927726, a.pstdev(), a.significantDigits());

  Helper::expectNear(2295675.0, b.mean(), a.significantDigits());
  Helper::expectNear(9041213360680.666, b.pvariance(), a.significantDigits());
  Helper::expectNear(3006861.0477839955, b.pstdev(), a.significantDigits());

  auto c = a.combine(b);
  EXPECT_EQ(6, c->count());
  Helper::expectNear(1147838.5, c->mean(), c->significantDigits());
  Helper::expectNear(5838135311072.917, c->pvariance(), c->significantDigits());
  Helper::expectNear(2416223.357033227, c->pstdev(), c->significantDigits());
}

class StatisticTest : public testing::Test {};

TEST(StatisticTest, CombineAcrossTypesFails) {
  HdrStatistic a;
  InMemoryStatistic b;
  StreamingStatistic c;
  EXPECT_THROW(a.combine(b), std::bad_cast);
  EXPECT_THROW(a.combine(c), std::bad_cast);
  EXPECT_THROW(b.combine(a), std::bad_cast);
  EXPECT_THROW(b.combine(c), std::bad_cast);
  EXPECT_THROW(c.combine(a), std::bad_cast);
  EXPECT_THROW(c.combine(b), std::bad_cast);
}

} // namespace Nighthawk

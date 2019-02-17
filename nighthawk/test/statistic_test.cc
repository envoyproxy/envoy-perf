#include <typeinfo> // std::bad_cast

#include "gtest/gtest.h"

#include "nighthawk/common/statistic.h"
#include "nighthawk/source/common/statistic_impl.h"

namespace Nighthawk {

using MyTypes =
    ::testing::Types<SimpleStatistic, InMemoryStatistic, HdrStatistic, StreamingStatistic>;

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

TYPED_TEST(TypedStatisticTest, Empty) {
  TypeParam a;
  EXPECT_EQ(0, a.count());
  EXPECT_TRUE(std::isnan(a.mean()));
  EXPECT_TRUE(std::isnan(a.pvariance()));
  EXPECT_TRUE(std::isnan(a.pstdev()));
}

TYPED_TEST(TypedStatisticTest, SingleAndDoubleValue) {
  TypeParam a;

  a.addValue(1);
  EXPECT_EQ(1, a.count());
  EXPECT_DOUBLE_EQ(1, a.mean());
  EXPECT_DOUBLE_EQ(0, a.pvariance());
  EXPECT_DOUBLE_EQ(0, a.pstdev());

  a.addValue(2);
  EXPECT_EQ(2, a.count());
  EXPECT_DOUBLE_EQ(1.5, a.mean());
  EXPECT_DOUBLE_EQ(0.25, a.pvariance());
  EXPECT_DOUBLE_EQ(0.5, a.pstdev());
}

TYPED_TEST(TypedStatisticTest, CatastrophicalCancellation) {
  // From https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
  // Assume that all floating point operations use standard IEEE 754 double-precision arithmetic.
  // Consider the sample (4, 7, 13, 16) from an infinite population. Based on this sample, the
  // estimated population mean is 10, and the unbiased estimate of population variance is 30. Both
  // the naïve algorithm and two-pass algorithm compute these values correctly.
  // Next consider the sample (108 + 4, 108 + 7, 108 + 13, 108 + 16), which gives rise to the same
  // estimated variance as the first sample. The two-pass algorithm computes this variance estimate
  // correctly, but the naïve algorithm returns 29.333333333333332 instead of 30. While this loss of
  // precision may be tolerable and viewed as a minor flaw of the naïve algorithm, further
  // increasing the offset makes the error catastrophic. Consider the sample (109 + 4, 109 + 7, 109
  // + 13, 109 + 16). Again the estimated population variance of 30 is computed correctly by the
  // two-pass algorithm, but the naïve algorithm now computes it as −170.66666666666666. This is a
  // serious problem with naïve algorithm and is due to catastrophic cancellation in the subtraction
  // of two similar numbers at the final stage of the algorithm.
  std::vector<int> values{4, 7, 13, 16};
  int exponential = 0;
  for (exponential = 3; exponential < 6; exponential++) {
    TypeParam a;
    double offset = std::pow(10, exponential);
    for (int value : values) {
      a.addValue(offset + value);
    }
    // If an implementation makes this claim, we put it to the test. SimpleStatistic is simple and
    // fast, but starts failing this test when exponential equals 8. HdrStatistic breaks at 5.
    // TODO(oschaaf): evaluate ^^
    if (a.resistsCatastrophicCancellation()) {
      Helper::expectNear(22.5, a.pvariance(), a.significantDigits());
      Helper::expectNear(4.7434164902525691, a.pstdev(), a.significantDigits());
    }
  }
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

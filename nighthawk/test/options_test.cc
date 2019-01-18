#include "gtest/gtest.h"

namespace Nighthawk {

class ClientOptionsTest : public testing::Test {

public:
  ClientOptionsTest() {}
  void SetUp() {}
  void TearDown() {}
};

TEST_F(ClientOptionsTest, TestTest) { EXPECT_EQ("hello", "hello"); }

} // namespace Nighthawk

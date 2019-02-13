#include "gtest/gtest.h"

#include "nighthawk/source/common/utility.h"

namespace Nighthawk {

class UtilityTest : public testing::Test {
public:
  UtilityTest() {}
  void checkUriParsing(const std::string& uri_to_test, const std::string& host_and_port,
                       const std::string& host_without_port, const uint64_t port,
                       const std::string& scheme, const std::string& path) {
    const Uri uri = Uri::Parse(uri_to_test);
    EXPECT_EQ(host_and_port, uri.host_and_port());
    EXPECT_EQ(host_without_port, uri.host_without_port());
    EXPECT_EQ(port, uri.port());
    EXPECT_EQ(scheme, uri.scheme());
    EXPECT_EQ(path, uri.path());
    EXPECT_TRUE(uri.isValid());
  }

  int32_t getCpuCountFromSet(cpu_set_t& set) { return CPU_COUNT(&set); }
};

TEST_F(UtilityTest, PerfectlyFineUrl) {
  checkUriParsing("http://a/b", "a:80", "a", 80, "http", "/b");
}

TEST_F(UtilityTest, Defaults) {
  checkUriParsing("a", "a:80", "a", 80, "http", "/");
  checkUriParsing("a/", "a:80", "a", 80, "http", "/");
  checkUriParsing("https://a", "a:443", "a", 443, "https", "/");
}

TEST_F(UtilityTest, SchemeIsLowerCased) {
  const Uri uri = Uri::Parse("HTTP://a");
  EXPECT_EQ("http", uri.scheme());
}

TEST_F(UtilityTest, ExplicitPort) {
  const Uri u1 = Uri::Parse("HTTP://a:111");
  EXPECT_EQ(111, u1.port());

  const Uri u2 = Uri::Parse("HTTP://a:-111");
  EXPECT_EQ(4294967185, u2.port());
  EXPECT_FALSE(u2.isValid());

  const Uri u3 = Uri::Parse("HTTP://a:0");
  EXPECT_FALSE(u2.isValid());
}

TEST_F(UtilityTest, SchemeWeDontUnderstand) {
  const Uri u = Uri::Parse("foo://a");
  EXPECT_FALSE(u.isValid());
}

// TODO(oschaaf): we probably want to move this out to another file.
TEST_F(UtilityTest, CpusWithAffinity) {
  cpu_set_t original_set;
  CPU_ZERO(&original_set);
  EXPECT_EQ(0, sched_getaffinity(0, sizeof(original_set), &original_set));

  uint32_t original_cpu_count = PlatformUtils::determineCpuCoresWithAffinity();
  EXPECT_EQ(original_cpu_count, getCpuCountFromSet(original_set));

  // Now the test, we set affinity to just the first cpu. We expect that to be reflected.
  // This will be a no-op on a single core system.
  cpu_set_t test_set;
  CPU_ZERO(&test_set);
  CPU_SET(0, &test_set);
  EXPECT_EQ(0, sched_setaffinity(0, sizeof(test_set), &test_set));
  EXPECT_EQ(1, PlatformUtils::determineCpuCoresWithAffinity());

  // Restore affinity to what it was.
  EXPECT_EQ(0, sched_setaffinity(0, sizeof(original_set), &original_set));
  EXPECT_EQ(original_cpu_count, PlatformUtils::determineCpuCoresWithAffinity());
}

} // namespace Nighthawk

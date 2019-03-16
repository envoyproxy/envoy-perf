#include <chrono>

#include "gtest/gtest.h"

#include "test/mocks/event/mocks.h"
#include "test/mocks/stats/mocks.h"

#include "test/test_common/utility.h"

#include "common/api/api_impl.h"

#include "nighthawk/test/mocks.h"

#include "nighthawk/source/client/client.h"
#include "nighthawk/source/client/option_interpreter_impl.h"
#include "nighthawk/source/client/options_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {
namespace Client {

class ClientTest : public testing::Test {
public:
  ClientTest() = default;

  std::unique_ptr<OptionsImpl> createOptionsImpl(const std::string& args) {
    std::vector<std::string> words = Envoy::TestUtility::split(args, ' ');
    std::vector<const char*> argv;
    for (const std::string& s : words) {
      argv.push_back(s.c_str());
    }
    return std::make_unique<OptionsImpl>(argv.size(), argv.data());
  }
};

TEST_F(ClientTest, NormalRun) {
  Main program(createOptionsImpl("foo --duration 1 --rps 1 --h2 https://www.google.com/"));
  EXPECT_TRUE(program.run());
}

TEST_F(ClientTest, AutoConcurrencyRun) {
  std::vector<const char*> argv;
  argv.push_back("foo");
  argv.push_back("--concurrency");
  argv.push_back("auto");
  argv.push_back("--duration");
  argv.push_back("1");
  argv.push_back("--rps");
  argv.push_back("1");
  argv.push_back("https://www.google.com/");

  Main program(argv.size(), argv.data());
  EXPECT_TRUE(program.run());
}

TEST_F(ClientTest, BadRun) {
  Main program(createOptionsImpl("foo --duration 1 --rps 1 --h2 https://unresolveable.host/"));
  EXPECT_FALSE(program.run());
}

} // namespace Client
} // namespace Nighthawk

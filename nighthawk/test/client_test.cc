#include <chrono>

#include "gtest/gtest.h"

#include "test/mocks/event/mocks.h"
#include "test/mocks/stats/mocks.h"

#include "test/integration/http_integration.h"
#include "test/integration/integration.h"
#include "test/integration/utility.h"
#include "test/server/utility.h"
#include "test/test_common/utility.h"

#include "common/api/api_impl.h"
#include "common/common/thread_impl.h"
#include "common/filesystem/filesystem_impl.h"

#include "nighthawk/test/mocks.h"

#include "nighthawk/source/client/client.h"
#include "nighthawk/source/client/factories_impl.h"
#include "nighthawk/source/client/options_impl.h"

using namespace std::chrono_literals;

namespace Nighthawk {
namespace Client {

class ClientTest : public Envoy::BaseIntegrationTest,
                   public testing::TestWithParam<Envoy::Network::Address::IpVersion> {
public:
  ClientTest() : Envoy::BaseIntegrationTest(GetParam(), realTime(), ClientTest::envoy_config) {}

  static void SetUpTestCase() {
    Envoy::Filesystem::InstanceImplPosix file_system;
    envoy_config = file_system.fileReadToEnd(Envoy::TestEnvironment::runfilesPath(
        "nighthawk/test/test_data/benchmark_http_client_test_envoy.yaml"));
    envoy_config = Envoy::TestEnvironment::substitute(envoy_config);
  }

  void SetUp() override {
    // We fork the integration test fixture into a child process, to avoid conflicting
    // runtimeloaders as both NH and the integration server want to own that and we can have only
    // one.
    pipe(fd);
    pid_ = fork();
    ASSERT(pid_ >= 0);
    if (pid_ == 0) {
      // child process
      ares_library_init(ARES_LIB_INIT_ALL);
      Envoy::Event::Libevent::Global::initialize();
      initialize();
      int port = lookupPort("listener_0");
      write(fd[1], &port, sizeof(port));

      // dummy read to wait for the parent to finish. fragile, but we can improve if
      // we decide the general approach is ok.
      sleep(1);
      ASSERT(read(fd[0], &port_, sizeof(port_)) == -1);
    } else if (pid_ > 0) {
      ASSERT(read(fd[0], &port_, sizeof(port_)) > 0);
      ASSERT(port_ > 0);
    }
  }

  void TearDown() override {
    if (pid_ == 0) {
      test_server_.reset();
      fake_upstreams_.clear();
      ares_library_cleanup();
    }
    close(fd[0]);
    close(fd[1]);
  }

  std::string testUrl() {
    ASSERT(pid_ > 0);
    const std::string address = Envoy::Network::Test::getLoopbackAddressUrlString(GetParam());
    return fmt::format("http://{}:{}/", address, port_);
  }

  std::unique_ptr<OptionsImpl> createOptionsImpl(const std::string& args) {
    std::vector<std::string> words = Envoy::TestUtility::split(args, ' ');
    std::vector<const char*> argv;
    for (const std::string& s : words) {
      argv.push_back(s.c_str());
    }
    return std::make_unique<OptionsImpl>(argv.size(), argv.data());
  }

  int port_;
  pid_t pid_;
  int fd[2];
  static std::string envoy_config;
};

std::string ClientTest::envoy_config;

INSTANTIATE_TEST_SUITE_P(IpVersions, ClientTest,
                         testing::ValuesIn(Envoy::TestEnvironment::getIpVersionsForTest()),
                         Envoy::TestUtility::ipTestParamsToString);

TEST_P(ClientTest, NormalRun) {
  if (pid_ > 0) {
    Main program(createOptionsImpl(fmt::format("foo --duration 2 --rps 10 {}", testUrl())));
    EXPECT_TRUE(program.run());
  }
}

TEST_P(ClientTest, AutoConcurrencyRun) {
  if (pid_ > 0) {
    std::vector<const char*> argv;
    argv.push_back("foo");
    argv.push_back("--concurrency");
    argv.push_back("auto");
    argv.push_back("--duration");
    argv.push_back("1");
    argv.push_back("--rps");
    argv.push_back("1");
    argv.push_back("--verbosity");
    argv.push_back("error");
    std::string url = testUrl();
    argv.push_back(url.c_str());

    Main program(argv.size(), argv.data());
    EXPECT_TRUE(program.run());
  }
}

TEST_P(ClientTest, BadRun) {
  if (pid_ > 0) {
    Main program(createOptionsImpl("foo --duration 1 --rps 1 https://unresolveable.host/"));
    EXPECT_FALSE(program.run());
  }
}

} // namespace Client
} // namespace Nighthawk

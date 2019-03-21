#include <chrono>

#include "ares.h"

#include "gtest/gtest.h"

#include "common/api/api_impl.h"
#include "common/common/compiler_requirements.h"
#include "common/common/thread_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/filesystem/filesystem_impl.h"
#include "common/http/header_map_impl.h"
#include "common/network/dns_impl.h"
#include "common/network/utility.h"
#include "common/runtime/runtime_impl.h"
#include "common/stats/isolated_store_impl.h"
#include "common/thread_local/thread_local_impl.h"

#include "nighthawk/source/client/benchmark_client_impl.h"
#include "nighthawk/source/common/platform_util_impl.h"
#include "nighthawk/source/common/rate_limiter_impl.h"
#include "nighthawk/source/common/sequencer_impl.h"
#include "nighthawk/source/common/statistic_impl.h"

#include "envoy/thread_local/thread_local.h"
#include "test/mocks/runtime/mocks.h"
#include "test/mocks/thread_local/mocks.h"

#include "test/integration/http_integration.h"

#include "test/integration/integration.h"
#include "test/integration/utility.h"
#include "test/server/utility.h"
#include "test/test_common/utility.h"

using namespace std::chrono_literals;

namespace Nighthawk {

class BenchmarkClientTest : public Envoy::BaseIntegrationTest,
                            public testing::TestWithParam<Envoy::Network::Address::IpVersion> {
public:
  BenchmarkClientTest()
      : Envoy::BaseIntegrationTest(GetParam(), realTime(), BenchmarkClientTest::envoy_config),
        api_(thread_factory_, store_, timeSystem()), dispatcher_(api_.allocateDispatcher()) {}

  static void copyFileToWorkingDir(const std::string path, const std::string path_to) {
    Envoy::Filesystem::InstanceImpl filesystem;
    const std::string content =
        filesystem.fileReadToEnd(Envoy::TestEnvironment::runfilesPath(path));
    Envoy::TestEnvironment::writeStringToFileForTest(path_to, content);
  }

  static void SetUpTestCase() {
    Envoy::Filesystem::InstanceImpl filesystem;
    envoy_config = filesystem.fileReadToEnd(Envoy::TestEnvironment::runfilesPath(
        "nighthawk/test/test_data/benchmark_http_client_test_envoy.yaml"));
    envoy_config = Envoy::TestEnvironment::substitute(envoy_config);
  }

  void SetUp() override {
    ares_library_init(ARES_LIB_INIT_ALL);
    Envoy::Event::Libevent::Global::initialize();
    BaseIntegrationTest::initialize();
  }

  uint32_t getTestServerHostAndPort() { return lookupPort("listener_0"); }

  uint32_t getTestServerHostAndSslPort() { return lookupPort("listener_1"); }

  void TearDown() override {
    if (client_.get() != nullptr) {
      client_->terminate();
    }
    test_server_.reset();
    fake_upstreams_.clear();
    tls_.shutdownGlobalThreading();
    ares_library_cleanup();
  }

  void setupBenchmarkClient(const std::string uriPath, bool use_https, bool use_h2,
                            uint32_t port = 0) {
    if (port == 0) {
      port = use_https ? getTestServerHostAndSslPort() : getTestServerHostAndPort();
    }

    std::string address =
        GetParam() == Envoy::Network::Address::IpVersion::v4 ? "127.0.0.1" : "[::1]";

    client_ = std::make_unique<Client::BenchmarkClientHttpImpl>(
        api_, *dispatcher_, std::make_unique<Envoy::Stats::IsolatedStoreImpl>(),
        std::make_unique<StreamingStatistic>(), std::make_unique<StreamingStatistic>(),
        fmt::format("{}://{}:{}{}", use_https ? "https" : "http", address, port, uriPath), use_h2);

    client_->setDnsLookupFamily(GetParam() == Envoy::Network::Address::IpVersion::v4
                                    ? Envoy::Network::DnsLookupFamily::V4Only
                                    : Envoy::Network::DnsLookupFamily::V6Only);
  }

  void testBasicFunctionality(const std::string uriPath, uint64_t max_pending,
                              uint64_t connection_limit, bool use_https, bool use_h2,
                              uint64_t amount_of_request) {
    setupBenchmarkClient(uriPath, use_https, use_h2);

    client_->setConnectionTimeout(10s);
    client_->setMaxPendingRequests(max_pending);
    client_->setConnectionLimit(connection_limit);
    EXPECT_TRUE(client_->initialize(runtime_));

    uint64_t amount = amount_of_request;
    uint64_t inflight_response_count = 0;

    std::function<void()> f = [this, &inflight_response_count]() {
      --inflight_response_count;
      if (inflight_response_count == 0) {
        dispatcher_->exit();
      }
    };

    for (uint64_t i = 0; i < amount; i++) {
      if (client_->tryStartOne(f)) {
        inflight_response_count++;
      }
    }

    EXPECT_EQ(max_pending, inflight_response_count);

    dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);

    EXPECT_EQ(0, getCounter("benchmark.stream_resets"));
  }

  uint64_t nonZeroValuedCounterCount() {
    Client::CounterFilter filter = [](std::string, uint64_t value) { return value > 0; };
    return client_->getCounters(filter).size();
  }

  uint64_t getCounter(std::string name) {
    auto counters = client_->getCounters();
    return counters["client." + name];
  }

  Envoy::Thread::ThreadFactoryImplPosix thread_factory_;
  Envoy::Stats::IsolatedStoreImpl store_;
  Envoy::Api::Impl api_;
  Envoy::Event::DispatcherPtr dispatcher_;
  Envoy::Runtime::RandomGeneratorImpl generator_;
  ::testing::NiceMock<Envoy::ThreadLocal::MockInstance> tls_;
  ::testing::NiceMock<Envoy::Runtime::MockLoader> runtime_;
  std::unique_ptr<Client::BenchmarkClientHttpImpl> client_;
  static std::string envoy_config;
};

std::string BenchmarkClientTest::envoy_config;

// TODO(oschaaf): test protocol violations, stream resets, etc.

INSTANTIATE_TEST_CASE_P(IpVersions, BenchmarkClientTest,
                        testing::ValuesIn(Envoy::TestEnvironment::getIpVersionsForTest()),
                        Envoy::TestUtility::ipTestParamsToString);

TEST_P(BenchmarkClientTest, BasicTestH1) {
  testBasicFunctionality("/lorem-ipsum-status-200", 1, 1, false, false, 10);

  EXPECT_EQ(1, getCounter("upstream_cx_http1_total"));
  EXPECT_LE(3621, getCounter("upstream_cx_rx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_cx_total"));
  EXPECT_LE(78, getCounter("upstream_cx_tx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_total"));
  EXPECT_EQ(1, getCounter("benchmark.http_2xx"));
  EXPECT_EQ(7, nonZeroValuedCounterCount());
}

TEST_P(BenchmarkClientTest, BasicTestH1404) {
  testBasicFunctionality("/lorem-ipsum-status-404", 1, 1, false, false, 10);

  EXPECT_EQ(1, getCounter("upstream_cx_http1_total"));
  EXPECT_EQ(0, getCounter("upstream_cx_protocol_error"));
  EXPECT_LE(97, getCounter("upstream_cx_rx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_cx_total"));
  EXPECT_LE(78, getCounter("upstream_cx_tx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_total"));
  EXPECT_EQ(1, getCounter("benchmark.http_4xx"));
  EXPECT_EQ(7, nonZeroValuedCounterCount());
}

TEST_P(BenchmarkClientTest, BasicTestHttpsH1) {
  testBasicFunctionality("/lorem-ipsum-status-200", 1, 1, true, false, 10);

  EXPECT_EQ(1, getCounter("ssl.ciphers.ECDHE-RSA-AES128-GCM-SHA256"));
  EXPECT_EQ(1, getCounter("ssl.curves.X25519"));
  EXPECT_EQ(1, getCounter("ssl.handshake"));
  EXPECT_EQ(1, getCounter("ssl.sigalgs.rsa_pss_rsae_sha256"));
  EXPECT_EQ(1, getCounter("ssl.versions.TLSv1.2"));
  EXPECT_EQ(1, getCounter("upstream_cx_http1_total"));
  EXPECT_LE(3622, getCounter("upstream_cx_rx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_cx_total"));
  EXPECT_LE(78, getCounter("upstream_cx_tx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_total"));
  EXPECT_EQ(1, getCounter("benchmark.http_2xx"));
  EXPECT_EQ(12, nonZeroValuedCounterCount());
}

TEST_P(BenchmarkClientTest, BasicTestH2) {
  testBasicFunctionality("/lorem-ipsum-status-200", 1, 1, true, true, 10);

  EXPECT_EQ(1, getCounter("ssl.ciphers.ECDHE-RSA-AES128-GCM-SHA256"));
  EXPECT_EQ(1, getCounter("ssl.curves.X25519"));
  EXPECT_EQ(1, getCounter("ssl.handshake"));
  EXPECT_EQ(1, getCounter("ssl.sigalgs.rsa_pss_rsae_sha256"));
  EXPECT_EQ(1, getCounter("ssl.versions.TLSv1.2"));
  EXPECT_EQ(1, getCounter("upstream_cx_http2_total"));
  EXPECT_LE(3585, getCounter("upstream_cx_rx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_cx_total"));
  EXPECT_LE(108, getCounter("upstream_cx_tx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_total"));
  EXPECT_EQ(1, getCounter("benchmark.http_2xx"));
  EXPECT_EQ(12, nonZeroValuedCounterCount());
}

TEST_P(BenchmarkClientTest, BasicTestH2C) {
  testBasicFunctionality("/lorem-ipsum-status-200", 1, 1, false, true, 10);

  EXPECT_EQ(1, getCounter("upstream_cx_http2_total"));
  EXPECT_LE(3584, getCounter("upstream_cx_rx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_cx_total"));
  EXPECT_LE(108, getCounter("upstream_cx_tx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_total"));
  EXPECT_EQ(1, getCounter("benchmark.http_2xx"));
  EXPECT_EQ(7, nonZeroValuedCounterCount());
}

// TODO(oschaaf): can't configure envoy to emit a weird status, fix
// this later.
TEST_P(BenchmarkClientTest, DISABLED_WeirdStatus) {
  testBasicFunctionality("/601", 1, 1, false, false, 10);

  EXPECT_EQ(1, getCounter("upstream_cx_http1_total"));
  EXPECT_LE(3621, getCounter("upstream_cx_rx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_cx_total"));
  EXPECT_LE(78, getCounter("upstream_cx_tx_bytes_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_total"));
  EXPECT_EQ(1, getCounter("benchmark.http_xxx"));
  EXPECT_EQ(7, nonZeroValuedCounterCount());
}

TEST_P(BenchmarkClientTest, H1ConnectionFailure) {
  // Kill the test server, so we can't connect.
  // We allow a single connection and no pending. We expect one connection failure.
  test_server_.reset();
  testBasicFunctionality("/lorem-ipsum-status-200", 1, 1, false, false, 10);

  EXPECT_EQ(1, getCounter("upstream_cx_connect_fail"));
  EXPECT_LE(1, getCounter("upstream_cx_http1_total"));
  EXPECT_EQ(1, getCounter("upstream_cx_total"));
  EXPECT_LE(1, getCounter("upstream_rq_pending_failure_eject"));
  EXPECT_EQ(1, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(1, getCounter("upstream_rq_total"));
  EXPECT_EQ(6, nonZeroValuedCounterCount());
}

TEST_P(BenchmarkClientTest, H1MultiConnectionFailure) {
  // Kill the test server, so we can't connect.
  // We allow ten connections and ten pending requests. We expect ten connection failures.
  test_server_.reset();
  testBasicFunctionality("/lorem-ipsum-status-200", 10, 10, false, false, 10);

  EXPECT_EQ(10, getCounter("upstream_cx_connect_fail"));
  EXPECT_LE(10, getCounter("upstream_cx_http1_total"));
  EXPECT_EQ(10, getCounter("upstream_cx_total"));
  EXPECT_LE(10, getCounter("upstream_rq_pending_failure_eject"));
  EXPECT_EQ(10, getCounter("upstream_rq_pending_total"));
  EXPECT_EQ(10, getCounter("upstream_rq_total"));
  EXPECT_EQ(6, nonZeroValuedCounterCount());
}

TEST_P(BenchmarkClientTest, EnableLatencyMeasurement) {
  setupBenchmarkClient("/", false, false);
  EXPECT_TRUE(client_->initialize(runtime_));

  EXPECT_EQ(false, client_->measureLatencies());

  int callback_count = 0;

  EXPECT_EQ(true, client_->tryStartOne([&]() {
    callback_count++;
    dispatcher_->exit();
  }));

  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);

  EXPECT_EQ(1, callback_count);

  EXPECT_EQ(0, client_->statistics()["benchmark_http_client.queue_to_connect"]->count());
  EXPECT_EQ(0, client_->statistics()["benchmark_http_client.request_to_response"]->count());

  client_->setMeasureLatencies(true);
  EXPECT_EQ(true, client_->measureLatencies());

  EXPECT_EQ(true, client_->tryStartOne([&]() {
    callback_count++;
    dispatcher_->exit();
  }));

  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);

  EXPECT_EQ(2, callback_count);

  EXPECT_EQ(1, client_->statistics()["benchmark_http_client.queue_to_connect"]->count());
  EXPECT_EQ(1, client_->statistics()["benchmark_http_client.request_to_response"]->count());
}

TEST_P(BenchmarkClientTest, UnresolvableHostname) {
  client_ = std::make_unique<Client::BenchmarkClientHttpImpl>(
      api_, *dispatcher_, std::make_unique<Envoy::Stats::IsolatedStoreImpl>(),
      std::make_unique<StreamingStatistic>(), std::make_unique<StreamingStatistic>(),
      fmt::format("http://unresolvablefoobarhost:80/"), false);

  EXPECT_FALSE(client_->initialize(runtime_));
}

TEST_P(BenchmarkClientTest, StatusTrackingInOnComplete) {
  client_ = std::make_unique<Client::BenchmarkClientHttpImpl>(
      api_, *dispatcher_, std::make_unique<Envoy::Stats::IsolatedStoreImpl>(),
      std::make_unique<StreamingStatistic>(), std::make_unique<StreamingStatistic>(),
      fmt::format("http://foo/"), false);
  Envoy::Http::HeaderMapImpl header;

  auto& status = header.insertStatus();

  status.value(1);
  client_->onComplete(true, header);

  status.value(100);
  client_->onComplete(true, header);

  status.value(200);
  client_->onComplete(true, header);

  status.value(300);
  client_->onComplete(true, header);

  status.value(400);
  client_->onComplete(true, header);

  status.value(500);
  client_->onComplete(true, header);

  status.value(600);
  client_->onComplete(true, header);

  status.value(200);
  // Shouldn't be counted by status, should add to stream reset.
  client_->onComplete(false, header);

  EXPECT_EQ(1, getCounter("benchmark.http_2xx"));
  EXPECT_EQ(1, getCounter("benchmark.http_3xx"));
  EXPECT_EQ(1, getCounter("benchmark.http_4xx"));
  EXPECT_EQ(1, getCounter("benchmark.http_5xx"));
  EXPECT_EQ(2, getCounter("benchmark.http_xxx"));
  EXPECT_EQ(1, getCounter("benchmark.stream_resets"));
}

} // namespace Nighthawk

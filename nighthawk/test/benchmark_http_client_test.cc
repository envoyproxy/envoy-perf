#include <chrono>

#include "ares.h"

#include "gtest/gtest.h"

#include "test/test_common/simulated_time_system.h"

#include "common/api/api_impl.h"
#include "common/common/compiler_requirements.h"
#include "common/common/thread_impl.h"
#include "common/event/dispatcher_impl.h"
#include "common/event/real_time_system.h"
#include "common/http/header_map_impl.h"
#include "common/network/utility.h"
#include "common/runtime/runtime_impl.h"
#include "common/stats/isolated_store_impl.h"

#include "client/benchmark_http_client.h"
#include "common/rate_limiter.h"
#include "common/sequencer.h"

#include "test/integration/integration.h"
#include "test/integration/utility.h"
#include "test/server/utility.h"
#include "test/test_common/utility.h"

using namespace std::chrono_literals;

namespace Nighthawk {

std::string lorem_ipsum_config;

class BenchmarkClientTest : public Envoy::BaseIntegrationTest,
                            public testing::TestWithParam<Envoy::Network::Address::IpVersion> {
public:
  BenchmarkClientTest()
      : Envoy::BaseIntegrationTest(GetParam(), realTime(), lorem_ipsum_config),
        api_(1000ms /*flush interval*/, thread_factory_, store_),
        dispatcher_(api_.allocateDispatcher(time_system_)), runtime_(generator_, store_, tls_) {}

  // Called once by the gtest framework before any BenchmarkClientTest are run.
  static void SetUpTestCase() {
    // TODO(oschaaf): ask around how we should do this.
    Envoy::TestEnvironment::setEnvVar("TEST_TMPDIR", Envoy::TestEnvironment::temporaryDirectory(),
                                      1);
    Envoy::TestEnvironment::exec({Envoy::TestEnvironment::runfilesPath("test/certs.sh")});

    const std::string body = R"EOF(
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam mauris felis, egestas eget turpis nec, ullamcorper laoreet magna. Donec ac condimentum lacus, nec semper eros. Sed iaculis arcu vitae egestas viverra. Nulla tempor, neque tempus tincidunt fermentum, orci nunc sagittis nisl, sed dapibus nunc ex sit amet justo. Ut porta pellentesque mi quis lobortis. Integer luctus, diam et mattis rhoncus, lacus orci condimentum tortor, vitae venenatis ante odio non massa. Duis ut nulla consectetur, elementum enim eu, maximus lacus. Ut id consequat libero. Mauris eget lorem et lorem iaculis laoreet a nec augue. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Maecenas ac cursus eros, ut eleifend lacus. Nam sit amet mauris nec mi luctus posuere. Phasellus ullamcorper vulputate purus sit amet dapibus. Mauris sit amet magna risus.

Sed venenatis nulla non massa tempus consectetur. In eu suscipit mi, auctor faucibus augue. Phasellus blandit sagittis urna sed semper. Maecenas sem purus, laoreet gravida pretium non, malesuada vitae felis. Nam laoreet nisi non ipsum tincidunt facilisis. Donec ultrices a elit vel aliquam. Duis et diam eu urna ultrices dictum. Etiam non nulla eu velit feugiat ultrices ac vitae orci. In id posuere magna, vitae vulputate lectus. Vestibulum consectetur luctus neque ut cursus. Aliquam vel dapibus sem, vel rhoncus elit. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. In consequat ipsum arcu, eget ultricies tellus finibus id.

Nam scelerisque viverra fermentum. Vivamus vitae tincidunt mauris. Cras id pretium lectus. Nunc ut leo vitae ligula dictum pretium. Proin et laoreet massa, sed pharetra ex. Nam nec pellentesque magna. Quisque lectus metus, ultrices eget nunc ac, blandit malesuada nulla. Nullam justo elit, eleifend eget elementum nec, convallis eu massa. Curabitur rhoncus pretium lorem et commodo. Morbi tincidunt lectus ut sodales pellentesque. Ut varius purus eget nunc ultricies congue.

Aliquam posuere blandit mollis. Integer quis sollicitudin mi. Integer ac lobortis felis. Maecenas a molestie libero, vitae rhoncus lacus. Phasellus est nunc, faucibus facilisis velit in, lobortis faucibus neque. Sed varius faucibus tristique. Sed maximus libero justo, sit amet laoreet orci feugiat eget. Pellentesque aliquet enim ut facilisis vestibulum. In lacinia malesuada quam, vitae aliquet arcu pretium eu. Aliquam cursus facilisis feugiat. Fusce eu orci ornare, tempus purus ac, commodo leo. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Sed tempus elit eget pretium volutpat. Sed tincidunt dapibus tortor at blandit.

Suspendisse vitae cursus elit. Sed pretium leo diam, ac semper nunc faucibus id. Sed pharetra, magna facilisis iaculis efficitur, nisl tortor vestibulum metus, id ultricies turpis arcu et odio. Suspendisse fringilla semper tincidunt. Cras at justo congue orci sodales efficitur. Donec quis sem ut dui efficitur faucibus. Pellentesque dapibus lacinia elit, sit amet volutpat velit gravida lobortis. Sed at purus eros. Pellentesque sodales, nulla at tincidunt placerat, massa metus facilisis nibh, non posuere ipsum metus a nisl. Duis nibh urna, laoreet quis interdum sed, tempor vel risus. Fusce tincidunt felis quis tincidunt luctus. Mauris vehicula ipsum magna, sed placerat ligula feugiat in. Curabitur pretium arcu magna, nec iaculis massa fermentum a.      
)EOF";

    const std::string file_path =
        Envoy::TestEnvironment::writeStringToFileForTest("lorem_ipsum.txt", body);

    lorem_ipsum_config = R"EOF(
admin:
  access_log_path: /dev/null
  address:
    socket_address:
      address: 127.0.0.1
      port_value: 0
static_resources:
  clusters:
    name: cluster_0
    hosts:
      socket_address:
        address: 127.0.0.1
        port_value: 0
  listeners:
  # define an origin server on :10000 that always returns "lorem ipsum..."
    - name: listener_0
      address:
        socket_address:
          address: 127.0.0.1
          port_value: 0
      filter_chains:
      - filters:
        - name: envoy.http_connection_manager
          config: 
            generate_request_id: false
            codec_type: auto
            stat_prefix: ingress_http
            route_config:
              name: local_route
              virtual_hosts:
              - name: service
                domains:
                - "*"
                routes:
                - match:
                    prefix: /
                  direct_response:
                    status: 200
                    body:
                      filename: {{ test_tmpdir }}/lorem_ipsum.txt
            http_filters:
            - name: envoy.router
              config:
                dynamic_stats: false
    - name: listener_1
      address:
        socket_address:
          address: 127.0.0.1
          port_value: 0
      filter_chains:
      - filters:
        - name: envoy.http_connection_manager
          config: 
            generate_request_id: false
            codec_type: auto
            stat_prefix: ingress_http
            route_config:
              name: local_route
              virtual_hosts:
              - name: service
                domains:
                - "*"
                routes:
                - match:
                    prefix: /
                  direct_response:
                    status: 200
                    body:
                      filename: {{ test_tmpdir }}/lorem_ipsum.txt
            http_filters:
            - name: envoy.router
              config:
                dynamic_stats: false
        tls_context:
          common_tls_context:
            tls_certificates:
              certificate_chain:
                filename: "{{ test_tmpdir }}/unittestcert.pem"
              private_key:
                filename: "{{ test_tmpdir }}/unittestkey.pem"
            validation_context:
              trusted_ca:
                filename: "{{ test_tmpdir }}/ca_cert.pem"
)EOF";
    lorem_ipsum_config = Envoy::TestEnvironment::substitute(lorem_ipsum_config);
  }

  void SetUp() override {
    ares_library_init(ARES_LIB_INIT_ALL);
    Envoy::Event::Libevent::Global::initialize();
    BaseIntegrationTest::initialize();
  }

  std::string getTestServerHostAndPort() {
    uint32_t port = lookupPort("listener_0");
    return fmt::format("127.0.0.1:{}", port);
  }

  std::string getTestServerHostAndSslPort() {
    uint32_t port = lookupPort("listener_1");
    return fmt::format("127.0.0.1:{}", port);
  }

  void TearDown() override {
    tls_.shutdownGlobalThreading();
    ares_library_cleanup();
    test_server_.reset();
    fake_upstreams_.clear();
  }

  Envoy::Thread::ThreadFactoryImplPosix thread_factory_;
  Envoy::Stats::IsolatedStoreImpl store_;
  Envoy::Event::RealTimeSystem time_system_;
  Envoy::Api::Impl api_;
  Envoy::Event::DispatcherPtr dispatcher_;
  Envoy::Runtime::RandomGeneratorImpl generator_;
  Envoy::ThreadLocal::InstanceImpl tls_;
  Envoy::Runtime::LoaderImpl runtime_;
};

INSTANTIATE_TEST_CASE_P(IpVersions, BenchmarkClientTest,
                        // testing::ValuesIn(Envoy::TestEnvironment::getIpVersionsForTest()),
                        testing::ValuesIn({Envoy::Network::Address::IpVersion::v4}),
                        Envoy::TestUtility::ipTestParamsToString);

// TODO(oschaaf): this is a very,very crude end-to-end test.
// Needs to be refactored and needs a synthetic origin to test
// against. also, we need more tests.
TEST_P(BenchmarkClientTest, BasicTestH1WithRequestQueue) {
  Envoy::Http::HeaderMapImplPtr request_headers = std::make_unique<Envoy::Http::HeaderMapImpl>();
  request_headers->insertMethod().value(Envoy::Http::Headers::get().MethodValues.Get);
  Client::BenchmarkHttpClient client(*dispatcher_, store_, time_system_,
                                     fmt::format("http://{}/", getTestServerHostAndPort()),
                                     std::move(request_headers), false /*use h2*/);

  int amount = 10;
  int inflight_response_count = 0;

  // Allow  request queueing so we can queue up everything all at once.
  client.set_connection_timeout(1s);
  client.set_max_pending_requests(amount);

  // TODO(oschaaf): either get rid of the intialize call, or test that we except
  // when we didn't call it before calling tryStartOne().  client.initialize(runtime_);
  client.initialize(runtime_);

  std::function<void()> f = [this, &inflight_response_count]() {
    if (--inflight_response_count == 0) {
      dispatcher_->exit();
    }
  };

  for (int i = 0; i < amount; i++) {
    if (client.tryStartOne(f)) {
      inflight_response_count++;
    }
  }

  EXPECT_EQ(amount, inflight_response_count);
  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);

  EXPECT_EQ(0, inflight_response_count);
  EXPECT_EQ(0, store_.counter("nighthawk.upstream_cx_connect_fail").value());
  EXPECT_EQ(0, client.http_bad_response_count());
  EXPECT_EQ(0, client.stream_reset_count());
  EXPECT_EQ(0, client.pool_overflow_failures());
  EXPECT_EQ(amount, client.http_good_response_count());
}

TEST_P(BenchmarkClientTest, BasicTestH1WithoutRequestQueue) {
  Envoy::Http::HeaderMapImplPtr request_headers = std::make_unique<Envoy::Http::HeaderMapImpl>();
  request_headers->insertMethod().value(Envoy::Http::Headers::get().MethodValues.Get);
  Client::BenchmarkHttpClient client(*dispatcher_, store_, time_system_,
                                     fmt::format("http://{}/", getTestServerHostAndPort()),
                                     std::move(request_headers), false /*use h2*/);

  client.set_connection_timeout(1s);
  client.set_max_pending_requests(1);
  client.initialize(runtime_);

  uint64_t amount = 10;
  uint64_t inflight_response_count = 0;

  std::function<void()> f = [this, &inflight_response_count]() {
    --inflight_response_count;
    if (inflight_response_count == 0) {
      dispatcher_->exit();
    }
  };

  for (uint64_t i = 0; i < amount; i++) {
    if (client.tryStartOne(f)) {
      inflight_response_count++;
    }
  }

  EXPECT_EQ(1, inflight_response_count);

  dispatcher_->run(Envoy::Event::Dispatcher::RunType::Block);

  EXPECT_EQ(0, inflight_response_count);
  EXPECT_EQ(0, store_.counter("nighthawk.upstream_cx_connect_fail").value());
  EXPECT_EQ(0, client.http_bad_response_count());
  EXPECT_EQ(0, client.stream_reset_count());
  // We throttle before the pool, so we expect no pool overflows.
  EXPECT_EQ(0, client.pool_overflow_failures());
  EXPECT_EQ(1, client.http_good_response_count());
}

// TODO(oschaaf): see figure out if we can and should simulated time in this test
// to eliminate flake chances, and speed up execution.
TEST_P(BenchmarkClientTest, SequencedH2Test) {
  Envoy::Http::HeaderMapImplPtr request_headers = std::make_unique<Envoy::Http::HeaderMapImpl>();
  request_headers->insertMethod().value(Envoy::Http::Headers::get().MethodValues.Get);

  Client::BenchmarkHttpClient client(*dispatcher_, store_, time_system_,
                                     fmt::format("https://{}/", getTestServerHostAndSslPort()),
                                     std::move(request_headers), true /*use h2*/);
  client.initialize(runtime_);

  // TODO(oschaaf): create an interface that pulls this from implementations upon implementation.
  SequencerTarget f =
      std::bind(&Client::BenchmarkHttpClient::tryStartOne, &client, std::placeholders::_1);

  LinearRateLimiter rate_limiter(time_system_, 1000ms);
  std::chrono::milliseconds duration(5999ms);
  Sequencer sequencer(*dispatcher_, time_system_, rate_limiter, f, duration, 10s);

  sequencer.start();
  sequencer.waitForCompletion();

  EXPECT_EQ(0, store_.counter("nighthawk.upstream_cx_connect_fail").value());
  EXPECT_EQ(0, client.http_bad_response_count());
  EXPECT_EQ(0, client.stream_reset_count());
  EXPECT_EQ(0, client.pool_overflow_failures());

  // We expect all responses to get in within the 999 ms slack we gave it.
  // TODO(oschaaf): under valgrind, on some systems, we overshoot here,
  // hence the EXPECT_LE.
  EXPECT_LE(5, client.http_good_response_count());
}

} // namespace Nighthawk

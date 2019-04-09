#include "test/integration/http_integration.h"

#include <sstream>

#include "gtest/gtest.h"

#include "common/api/api_impl.h"
#include "envoy/upstream/cluster_manager.h"
#include "envoy/upstream/upstream.h"
#include "test/common/upstream/utility.h"

#include "nighthawk/source/server/http_test_origin_filter.h"

namespace Nighthawk {

class HttpTestOriginIntegrationTest
    : public Envoy::HttpIntegrationTest,
      public testing::TestWithParam<Envoy::Network::Address::IpVersion> {
public:
  HttpTestOriginIntegrationTest()
      : HttpIntegrationTest(Envoy::Http::CodecClient::Type::HTTP1, GetParam(), realTime()) {}
  void SetUp() override { initialize(); }

  void initialize() override {
    config_helper_.addFilter(R"EOF(
name: test-origin
config:
    key: x-supplied-by
    val: nighthawk-test-origin
)EOF");
    HttpIntegrationTest::initialize();
  }

  // TODO(oschaaf): Modify Envoy's version to allow for a way to manipulate the request headers
  // before they get send. Then we can eliminate these copies
  // ofEnvoy::IntegrationUtil::makeSingleRequest().
  Envoy::BufferingStreamDecoderPtr
  makeSingleRequest(uint32_t port, const std::string& method, const std::string& url,
                    const std::string& body, Envoy::Http::CodecClient::Type type,
                    Envoy::Network::Address::IpVersion ip_version, const std::string& host,
                    const std::string& content_type,
                    std::function<void(Envoy::Http::HeaderMapImpl&)> request_header_delegate) {
    auto addr = Envoy::Network::Utility::resolveUrl(fmt::format(
        "tcp://{}:{}", Envoy::Network::Test::getLoopbackAddressUrlString(ip_version), port));
    return makeSingleRequest(addr, method, url, body, type, host, content_type,
                             request_header_delegate);
  }

  Envoy::BufferingStreamDecoderPtr
  makeSingleRequest(const Envoy::Network::Address::InstanceConstSharedPtr& addr,
                    const std::string& method, const std::string& url, const std::string& body,
                    Envoy::Http::CodecClient::Type type, const std::string& host,
                    const std::string& content_type,
                    std::function<void(Envoy::Http::HeaderMapImpl&)> request_header_delegate) {

    testing::NiceMock<Envoy::Stats::MockIsolatedStatsStore> mock_stats_store;
    Envoy::Event::GlobalTimeSystem time_system;
    Envoy::Api::Impl api(Envoy::Thread::threadFactoryForTest(), mock_stats_store, time_system,
                         Envoy::Filesystem::fileSystemForTest());
    Envoy::Event::DispatcherPtr dispatcher(api.allocateDispatcher());
    std::shared_ptr<Envoy::Upstream::MockClusterInfo> cluster{
        new testing::NiceMock<Envoy::Upstream::MockClusterInfo>()};
    Envoy::Upstream::HostDescriptionConstSharedPtr host_description{
        Envoy::Upstream::makeTestHostDescription(cluster, "tcp://127.0.0.1:80")};
    Envoy::Http::CodecClientProd client(
        type,
        dispatcher->createClientConnection(addr, Envoy::Network::Address::InstanceConstSharedPtr(),
                                           Envoy::Network::Test::createRawBufferSocket(), nullptr),
        host_description, *dispatcher);
    Envoy::BufferingStreamDecoderPtr response(new Envoy::BufferingStreamDecoder([&]() -> void {
      client.close();
      dispatcher->exit();
    }));
    Envoy::Http::StreamEncoder& encoder = client.newStream(*response);
    encoder.getStream().addCallbacks(*response);

    Envoy::Http::HeaderMapImpl headers;
    headers.insertMethod().value(method);
    headers.insertPath().value(url);
    headers.insertHost().value(host);
    headers.insertScheme().value(Envoy::Http::Headers::get().SchemeValues.Http);
    if (!content_type.empty()) {
      headers.insertContentType().value(content_type);
    }
    request_header_delegate(headers);
    encoder.encodeHeaders(headers, body.empty());
    if (!body.empty()) {
      Envoy::Buffer::OwnedImpl body_buffer(body);
      encoder.encodeData(body_buffer, true);
    }

    dispatcher->run(Envoy::Event::Dispatcher::RunType::Block);
    return response;
  }

  void testWithResponseSize(int response_size) {
    std::stringstream ss;
    int i = response_size;
    while (i > 0) {
      ss << "a";
      i--;
    }

    Envoy::BufferingStreamDecoderPtr response = makeSingleRequest(
        lookupPort("http"), "GET", "/", "", downstream_protocol_, version_, "foo.com", "",
        [response_size](Envoy::Http::HeaderMapImpl& request_headers) {
          const std::string header_value(std::to_string(response_size));
          request_headers.addCopy(
              Nighthawk::Server::TestOrigin::HeaderNames::get().TestOriginResponseSize,
              header_value);
        });
    ASSERT_TRUE(response->complete());
    EXPECT_STREQ("200", response->headers().Status()->value().c_str());
    auto inserted_header = response->headers().get(Envoy::Http::LowerCaseString("x-supplied-by"));
    ASSERT_NE(nullptr, inserted_header);
    EXPECT_STREQ("nighthawk-test-origin", inserted_header->value().c_str());
    EXPECT_STREQ("text/plain", response->headers().ContentType()->value().c_str());
    EXPECT_EQ(ss.str(), response->body());
  }

  void testBadInput(int response_size) {
    Envoy::BufferingStreamDecoderPtr response = makeSingleRequest(
        lookupPort("http"), "GET", "/", "", downstream_protocol_, version_, "foo.com", "",
        [response_size](Envoy::Http::HeaderMapImpl& request_headers) {
          const std::string header_value(std::to_string(response_size));
          request_headers.addCopy(
              Nighthawk::Server::TestOrigin::HeaderNames::get().TestOriginResponseSize,
              std::to_string(response_size));
        });
    ASSERT_TRUE(response->complete());
    EXPECT_STREQ("500", response->headers().Status()->value().c_str());
  }
};

INSTANTIATE_TEST_CASE_P(IpVersions, HttpTestOriginIntegrationTest,
                        testing::ValuesIn(Envoy::TestEnvironment::getIpVersionsForTest()));

TEST_P(HttpTestOriginIntegrationTest, TestNoSizeIndicationFails) {
  Envoy::BufferingStreamDecoderPtr response =
      makeSingleRequest(lookupPort("http"), "GET", "/", "", downstream_protocol_, version_,
                        "foo.com", "", [](Envoy::Http::HeaderMapImpl&) {});
  ASSERT_TRUE(response->complete());
  EXPECT_STREQ("500", response->headers().Status()->value().c_str());
}

TEST_P(HttpTestOriginIntegrationTest, TestBasics) {
  testWithResponseSize(10);
  testWithResponseSize(100);
  testWithResponseSize(1000);
  testWithResponseSize(10000);
}

TEST_P(HttpTestOriginIntegrationTest, TestNegative) { testBadInput(-1); }

TEST_P(HttpTestOriginIntegrationTest, TestTooLarge) {
  const int max = 1024 * 1024 * 4;
  testBadInput(max + 1);
}

} // namespace Nighthawk

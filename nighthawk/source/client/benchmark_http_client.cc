#include "client/benchmark_http_client.h"

#include "common/http/utility.h"
#include "common/network/utility.h"

#include "ares.h"

#include "absl/strings/str_split.h"

#include "common/api/api_impl.h"
#include "common/common/compiler_requirements.h"
#include "common/event/dispatcher_impl.h"
#include "common/http/header_map_impl.h"
#include "common/http/headers.h"
#include "common/http/http1/conn_pool.h"
#include "common/http/http2/conn_pool.h"
#include "common/network/raw_buffer_socket.h"
#include "common/network/utility.h"
#include "common/runtime/runtime_impl.h"
#include "common/thread_local/thread_local_impl.h"
#include "common/upstream/cluster_manager_impl.h"

#include "common/ssl.h"
#include "common/stream_decoder.h"

using namespace std::chrono_literals;

namespace Nighthawk {
namespace Client {

BenchmarkHttpClient::BenchmarkHttpClient(Envoy::Event::Dispatcher& dispatcher,
                                         Envoy::Stats::Store& store, Envoy::TimeSource& time_source,
                                         std::string uri,
                                         Envoy::Http::HeaderMapImplPtr&& request_headers,
                                         bool use_h2)
    : dispatcher_(dispatcher), store_(store), time_source_(time_source),
      request_headers_(std::move(request_headers)), use_h2_(use_h2), is_https_(false), host_(""),
      port_(0), path_("/"), dns_failure_(true), timeout_(5s), connection_limit_(1),
      max_pending_requests_(1), pool_overflow_failures_(0), stream_reset_count_(0),
      http_good_response_count_(0), http_bad_response_count_(0), requests_completed_(0),
      requests_initiated_(0) {

  // parse incoming uri into fields that we need.
  // TODO(oschaaf): refactor. also input validation, etc.
  absl::string_view host, path;
  Envoy::Http::Utility::extractHostPathFromUri(uri, host, path);
  host_ = std::string(host);
  path_ = std::string(path);

  size_t colon_index = host_.find(':');
  is_https_ = uri.find("https://") == 0;

  if (colon_index == std::string::npos) {
    port_ = is_https_ ? 443 : 80;
  } else {
    std::string tcp_url = fmt::format("tcp://{}", this->host_);
    port_ = Envoy::Network::Utility::portFromTcpUrl(tcp_url);
    host_ = host_.substr(0, colon_index);
  }

  request_headers_->insertPath().value(path_);
  request_headers_->insertHost().value(host_);
  request_headers_->insertScheme().value(is_https_ ? Envoy::Http::Headers::get().SchemeValues.Https
                                                   : Envoy::Http::Headers::get().SchemeValues.Http);
}

BenchmarkHttpClient::~BenchmarkHttpClient() {}

void BenchmarkHttpClient::syncResolveDns() {
  auto dns_resolver = dispatcher_.createDnsResolver({});
  Envoy::Network::ActiveDnsQuery* active_dns_query_ = dns_resolver->resolve(
      host_, Envoy::Network::DnsLookupFamily::V4Only,
      [this, &active_dns_query_](
          const std::list<Envoy::Network::Address::InstanceConstSharedPtr>&& address_list) -> void {
        active_dns_query_ = nullptr;
        ENVOY_LOG(debug, "DNS resolution complete for {} ({} entries).", this->host_,
                  address_list.size());
        if (!address_list.empty()) {
          dns_failure_ = false;
          target_address_ =
              Envoy::Network::Utility::getAddressWithPort(*address_list.front(), port_);
        } else {
          ENVOY_LOG(critical, "Could not resolve host [{}]", host_);
        }
        dispatcher_.exit();
      });
  // Wait for DNS resolution to complete before proceeding.
  dispatcher_.run(Envoy::Event::Dispatcher::RunType::Block);
}

void BenchmarkHttpClient::initialize(Envoy::Runtime::LoaderImpl& runtime) {
  syncResolveDns();

  envoy::api::v2::Cluster cluster_config;
  envoy::api::v2::core::BindConfig bind_config;
  // envoy::config::bootstrap::v2::Runtime runtime_config;

  auto thresholds = cluster_config.mutable_circuit_breakers()->add_thresholds();

  cluster_config.mutable_connect_timeout()->set_seconds(timeout_.count());
  thresholds->mutable_max_retries()->set_value(0);
  thresholds->mutable_max_connections()->set_value(connection_limit_);
  thresholds->mutable_max_pending_requests()->set_value(max_pending_requests_);

  Envoy::Stats::ScopePtr scope = store_.createScope(fmt::format(
      "nighthawk.{}", cluster_config.alt_stat_name().empty() ? cluster_config.name()
                                                             : cluster_config.alt_stat_name()));

  Envoy::Network::TransportSocketFactoryPtr socket_factory;
  if (is_https_) {
    socket_factory = Envoy::Network::TransportSocketFactoryPtr{
        new Ssl::MClientSslSocketFactory(store_, time_source_, use_h2_)};
  } else {
    socket_factory = std::make_unique<Envoy::Network::RawBufferSocketFactory>();
  };

  cluster_ = std::make_unique<Envoy::Upstream::ClusterInfoImpl>(
      cluster_config, bind_config, runtime, std::move(socket_factory), std::move(scope),
      false /*added_via_api*/);

  Envoy::Network::ConnectionSocket::OptionsSharedPtr options =
      std::make_shared<Envoy::Network::ConnectionSocket::Options>();

  auto host = std::shared_ptr<Envoy::Upstream::Host>{new Envoy::Upstream::HostImpl(
      cluster_, host_, target_address_, envoy::api::v2::core::Metadata::default_instance(),
      1 /* weight */, envoy::api::v2::core::Locality(),
      envoy::api::v2::endpoint::Endpoint::HealthCheckConfig::default_instance(), 0)};

  if (use_h2_) {
    pool_ = std::make_unique<Envoy::Http::Http2::ProdConnPoolImpl>(
        dispatcher_, host, Envoy::Upstream::ResourcePriority::Default, options);
  } else {
    pool_ = std::make_unique<Envoy::Http::Http1::ConnPoolImplProd>(
        dispatcher_, host, Envoy::Upstream::ResourcePriority::Default, options);
  }
}

bool BenchmarkHttpClient::tryStartOne(std::function<void()> caller_completion_callback) {
  // NOTE(oschaaf): We can't rely on resourceManager()::requests() because that
  // isn't used for h/1.
  if (!cluster_->resourceManager(Envoy::Upstream::ResourcePriority::Default)
           .pendingRequests()
           .canCreate() /*||
      
      TODO(oschaaf): this improves accuracy, but breaks the tests because
      those rely on pending requests functional to queue up requests.
      Revisit this later.

      (requests_initiated_ - requests_completed_) >= connection_limit_*/) {
    return false;
  }

  auto stream_decoder = new Nighthawk::Http::StreamDecoder(caller_completion_callback, *this);
  requests_initiated_++;
  pool_->newStream(*stream_decoder, *this);

  return true;
}

void BenchmarkHttpClient::onComplete(bool success, const Envoy::Http::HeaderMap& headers) {
  requests_completed_++;
  if (!success) {
    stream_reset_count_++;
  } else {
    ASSERT(headers.Status());
    int64_t status = Envoy::Http::Utility::getResponseStatus(headers);
    // TODO(oschaaf): we can very probably pull these from the stats.
    if (status >= 400 && status <= 599) {
      http_bad_response_count_++;
    } else {
      http_good_response_count_++;
    }
  }
}

void BenchmarkHttpClient::onPoolFailure(Envoy::Http::ConnectionPool::PoolFailureReason reason,
                                        Envoy::Upstream::HostDescriptionConstSharedPtr) {
  switch (reason) {
  case Envoy::Http::ConnectionPool::PoolFailureReason::ConnectionFailure:
    break;
  case Envoy::Http::ConnectionPool::PoolFailureReason::Overflow:
    pool_overflow_failures_++;
    break;
  default:
    ASSERT(false);
  }
}

void BenchmarkHttpClient::onPoolReady(Envoy::Http::StreamEncoder& encoder,
                                      Envoy::Upstream::HostDescriptionConstSharedPtr) {
  encoder.encodeHeaders(*request_headers_, true);
}

} // namespace Client
} // namespace Nighthawk
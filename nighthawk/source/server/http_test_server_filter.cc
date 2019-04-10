#include <sstream>
#include <string>

#include "absl/strings/numbers.h"

#include "http_test_server_filter.h"

#include "envoy/server/filter_config.h"

namespace Nighthawk {
namespace Server {

HttpTestServerDecoderFilterConfig::HttpTestServerDecoderFilterConfig(
    const nighthawk::server::TestServer& proto_config)
    : key_(proto_config.key()), val_(proto_config.val()) {}

HttpTestServerDecoderFilter::HttpTestServerDecoderFilter(
    HttpTestServerDecoderFilterConfigSharedPtr config)
    : config_(config) {}

HttpTestServerDecoderFilter::~HttpTestServerDecoderFilter() {}

void HttpTestServerDecoderFilter::onDestroy() {}

Envoy::Http::LowerCaseString HttpTestServerDecoderFilter::headerKey() const {
  return Envoy::Http::LowerCaseString(config_->key());
}

const std::string& HttpTestServerDecoderFilter::headerValue() const { return config_->val(); }

Envoy::Http::FilterHeadersStatus
HttpTestServerDecoderFilter::decodeHeaders(Envoy::Http::HeaderMap& headers, bool) {
  const auto response_size_header =
      headers.get(TestServer::HeaderNames::get().TestServerResponseSize);
  const int max = 1024 * 1024 * 4;
  int response_size = -1;

  if (response_size_header != nullptr &&
      absl::SimpleAtoi(response_size_header->value().c_str(), &response_size) &&
      response_size >= 0 && response_size < max) {
    decoder_callbacks_->sendLocalReply(
        static_cast<Envoy::Http::Code>(200), std::string(response_size, 'a'),
        [this](Envoy::Http::HeaderMap& direct_response_headers) {
          direct_response_headers.addCopy(headerKey(), headerValue());
        },
        absl::nullopt);
  } else {
    decoder_callbacks_->sendLocalReply(static_cast<Envoy::Http::Code>(500),
                                       "test-server didn't understand the request", nullptr,
                                       absl::nullopt);
  }
  return Envoy::Http::FilterHeadersStatus::StopIteration;
}

Envoy::Http::FilterDataStatus HttpTestServerDecoderFilter::decodeData(Envoy::Buffer::Instance&,
                                                                      bool) {
  return Envoy::Http::FilterDataStatus::Continue;
}

Envoy::Http::FilterTrailersStatus
HttpTestServerDecoderFilter::decodeTrailers(Envoy::Http::HeaderMap&) {
  return Envoy::Http::FilterTrailersStatus::Continue;
}

void HttpTestServerDecoderFilter::setDecoderFilterCallbacks(
    Envoy::Http::StreamDecoderFilterCallbacks& callbacks) {
  decoder_callbacks_ = &callbacks;
}

} // namespace Server
} // namespace Nighthawk

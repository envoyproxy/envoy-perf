#include <sstream>
#include <string>

#include "absl/strings/numbers.h"

#include "http_test_origin_filter.h"

#include "envoy/server/filter_config.h"

namespace Nighthawk {
namespace Server {

HttpTestOriginDecoderFilterConfig::HttpTestOriginDecoderFilterConfig(
    const nighthawk::server::TestOrigin& proto_config)
    : key_(proto_config.key()), val_(proto_config.val()) {}

HttpTestOriginDecoderFilter::HttpTestOriginDecoderFilter(
    HttpTestOriginDecoderFilterConfigSharedPtr config)
    : config_(config) {}

HttpTestOriginDecoderFilter::~HttpTestOriginDecoderFilter() {}

void HttpTestOriginDecoderFilter::onDestroy() {}

const Envoy::Http::LowerCaseString HttpTestOriginDecoderFilter::headerKey() const {
  return Envoy::Http::LowerCaseString(config_->key());
}

const std::string HttpTestOriginDecoderFilter::headerValue() const { return config_->val(); }

Envoy::Http::FilterHeadersStatus
HttpTestOriginDecoderFilter::decodeHeaders(Envoy::Http::HeaderMap& headers, bool) {
  const auto response_size_header =
      headers.get(TestOrigin::HeaderNames::get().TestOriginResponseSize);
  const int max = 1024 * 1024 * 4;
  int response_size = -1;

  if (response_size_header != nullptr &&
      absl::SimpleAtoi(response_size_header->value().c_str(), &response_size) &&
      response_size >= 0 && response_size < max) {
    // TODO(oschaaf): We can optimize this.
    std::stringstream stream;
    while (response_size--) {
      stream << "a";
    }
    decoder_callbacks_->sendLocalReply(static_cast<Envoy::Http::Code>(200), stream.str(),
                                       [this](Envoy::Http::HeaderMap& direct_response_headers) {
                                         direct_response_headers.addCopy(headerKey(),
                                                                         headerValue());
                                       },
                                       absl::nullopt);

  } else {
    decoder_callbacks_->sendLocalReply(static_cast<Envoy::Http::Code>(500),
                                       "test-origin didn't understand the request", nullptr,
                                       absl::nullopt);
  }
  return Envoy::Http::FilterHeadersStatus::StopIteration;
}

Envoy::Http::FilterDataStatus HttpTestOriginDecoderFilter::decodeData(Envoy::Buffer::Instance&,
                                                                      bool) {
  return Envoy::Http::FilterDataStatus::Continue;
}

Envoy::Http::FilterTrailersStatus
HttpTestOriginDecoderFilter::decodeTrailers(Envoy::Http::HeaderMap&) {
  return Envoy::Http::FilterTrailersStatus::Continue;
}

void HttpTestOriginDecoderFilter::setDecoderFilterCallbacks(
    Envoy::Http::StreamDecoderFilterCallbacks& callbacks) {
  decoder_callbacks_ = &callbacks;
}

} // namespace Server
} // namespace Nighthawk

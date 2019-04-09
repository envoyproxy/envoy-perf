#include <sstream>
#include <string>

#include "absl/strings/numbers.h"

#include "http_test_origin_filter.h"

#include "envoy/server/filter_config.h"

namespace Envoy {
namespace Http {

HttpTestOriginDecoderFilterConfig::HttpTestOriginDecoderFilterConfig(
    const nighthawk::server::TestOrigin& proto_config)
    : key_(proto_config.key()), val_(proto_config.val()) {}

HttpTestOriginDecoderFilter::HttpTestOriginDecoderFilter(
    HttpTestOriginDecoderFilterConfigSharedPtr config)
    : config_(config) {}

HttpTestOriginDecoderFilter::~HttpTestOriginDecoderFilter() {}

void HttpTestOriginDecoderFilter::onDestroy() {}

const LowerCaseString HttpTestOriginDecoderFilter::headerKey() const {
  return LowerCaseString(config_->key());
}

const std::string HttpTestOriginDecoderFilter::headerValue() const { return config_->val(); }

FilterHeadersStatus HttpTestOriginDecoderFilter::decodeHeaders(HeaderMap& headers, bool) {
  const auto header_name = Envoy::Http::LowerCaseString("x-test-origin-response-size");
  const auto response_size_header = headers.get(header_name);
  const int max = 1024 * 1024 * 4;
  int response_size = -1;

  if (response_size_header != nullptr &&
      absl::SimpleAtoi(response_size_header->value().c_str(), &response_size) &&
      response_size >= 0 && response_size < max) {
    std::stringstream stream;
    while (response_size--) {
      stream << "a";
    }
    decoder_callbacks_->sendLocalReply(static_cast<Http::Code>(200), stream.str(),
                                       [this](Envoy::Http::HeaderMap& direct_response_headers) {
                                         direct_response_headers.addCopy(headerKey(),
                                                                         headerValue());
                                       },
                                       absl::nullopt);

  } else {
    decoder_callbacks_->sendLocalReply(static_cast<Http::Code>(500),
                                       "test-origin didn't understand the request", nullptr,
                                       absl::nullopt);
  }
  return FilterHeadersStatus::StopIteration;
}

FilterDataStatus HttpTestOriginDecoderFilter::decodeData(Buffer::Instance&, bool) {
  return FilterDataStatus::Continue;
}

FilterTrailersStatus HttpTestOriginDecoderFilter::decodeTrailers(HeaderMap&) {
  return FilterTrailersStatus::Continue;
}

void HttpTestOriginDecoderFilter::setDecoderFilterCallbacks(
    StreamDecoderFilterCallbacks& callbacks) {
  decoder_callbacks_ = &callbacks;
}

} // namespace Http
} // namespace Envoy

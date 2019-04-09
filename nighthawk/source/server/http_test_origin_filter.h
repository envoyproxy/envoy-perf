#pragma once

#include <string>

#include "envoy/server/filter_config.h"

#include "nighthawk/source/server/http_test_origin_filter.pb.h"

namespace Envoy {
namespace Http {

class HttpTestOriginDecoderFilterConfig {
public:
  HttpTestOriginDecoderFilterConfig(const nighthawk::server::TestOrigin& proto_config);

  const std::string& key() const { return key_; }
  const std::string& val() const { return val_; }

private:
  const std::string key_;
  const std::string val_;
};

typedef std::shared_ptr<HttpTestOriginDecoderFilterConfig>
    HttpTestOriginDecoderFilterConfigSharedPtr;

class HttpTestOriginDecoderFilter : public StreamDecoderFilter {
public:
  HttpTestOriginDecoderFilter(HttpTestOriginDecoderFilterConfigSharedPtr);
  ~HttpTestOriginDecoderFilter();

  // Http::StreamFilterBase
  void onDestroy() override;

  // Http::StreamDecoderFilter
  FilterHeadersStatus decodeHeaders(HeaderMap&, bool) override;
  FilterDataStatus decodeData(Buffer::Instance&, bool) override;
  FilterTrailersStatus decodeTrailers(HeaderMap&) override;
  void setDecoderFilterCallbacks(StreamDecoderFilterCallbacks&) override;

private:
  const HttpTestOriginDecoderFilterConfigSharedPtr config_;
  StreamDecoderFilterCallbacks* decoder_callbacks_;

  const LowerCaseString headerKey() const;
  const std::string headerValue() const;
};

} // namespace Http
} // namespace Envoy

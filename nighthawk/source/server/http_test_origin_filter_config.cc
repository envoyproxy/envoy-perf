#include <string>

#include "http_test_origin_filter.h"

#include "common/config/json_utility.h"
#include "envoy/registry/registry.h"

#include "nighthawk/source/server/http_test_origin_filter.pb.h"
#include "nighthawk/source/server/http_test_origin_filter.pb.validate.h"

namespace Nighthawk {
namespace Server {
namespace Configuration {

class HttpTestOriginDecoderFilterConfig
    : public Envoy::Server::Configuration::NamedHttpFilterConfigFactory {
public:
  Envoy::Http::FilterFactoryCb
  createFilterFactory(const Envoy::Json::Object& json_config, const std::string&,
                      Envoy::Server::Configuration::FactoryContext& context) override {

    nighthawk::server::TestOrigin proto_config;
    translateHttpTestOriginDecoderFilter(json_config, proto_config);

    return createFilter(proto_config, context);
  }

  Envoy::Http::FilterFactoryCb
  createFilterFactoryFromProto(const Envoy::Protobuf::Message& proto_config, const std::string&,
                               Envoy::Server::Configuration::FactoryContext& context) override {

    return createFilter(
        Envoy::MessageUtil::downcastAndValidate<const nighthawk::server::TestOrigin&>(proto_config),
        context);
  }

  /**
   *  Return the Protobuf Message that represents your config incase you have config proto
   */
  Envoy::ProtobufTypes::MessagePtr createEmptyConfigProto() override {
    return Envoy::ProtobufTypes::MessagePtr{new nighthawk::server::TestOrigin()};
  }

  std::string name() override { return "test-origin"; }

private:
  Envoy::Http::FilterFactoryCb createFilter(const nighthawk::server::TestOrigin& proto_config,
                                            Envoy::Server::Configuration::FactoryContext&) {
    Envoy::Http::HttpTestOriginDecoderFilterConfigSharedPtr config =
        std::make_shared<Envoy::Http::HttpTestOriginDecoderFilterConfig>(
            Envoy::Http::HttpTestOriginDecoderFilterConfig(proto_config));

    return [config](Envoy::Http::FilterChainFactoryCallbacks& callbacks) -> void {
      auto filter = new Envoy::Http::HttpTestOriginDecoderFilter(config);
      callbacks.addStreamDecoderFilter(Envoy::Http::StreamDecoderFilterSharedPtr{filter});
    };
  }

  void translateHttpTestOriginDecoderFilter(const Envoy::Json::Object& json_config,
                                            nighthawk::server::TestOrigin& proto_config) {

    // normally we want to validate the json_config againts a defined json-schema here.
    JSON_UTIL_SET_STRING(json_config, proto_config, key);
    JSON_UTIL_SET_STRING(json_config, proto_config, val);
  }
};

/**
 * Static registration for this test-origin filter. @see RegisterFactory.
 */
static Envoy::Registry::RegisterFactory<HttpTestOriginDecoderFilterConfig,
                                        Envoy::Server::Configuration::NamedHttpFilterConfigFactory>
    register_;

} // namespace Configuration
} // namespace Server
} // namespace Nighthawk

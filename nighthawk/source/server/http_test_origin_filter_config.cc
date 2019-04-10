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
  createFilterFactory(const Envoy::Json::Object&, const std::string&,
                      Envoy::Server::Configuration::FactoryContext&) override {
    NOT_IMPLEMENTED_GCOVR_EXCL_LINE;
  }

  Envoy::Http::FilterFactoryCb
  createFilterFactoryFromProto(const Envoy::Protobuf::Message& proto_config, const std::string&,
                               Envoy::Server::Configuration::FactoryContext& context) override {

    return createFilter(
        Envoy::MessageUtil::downcastAndValidate<const nighthawk::server::TestOrigin&>(proto_config),
        context);
  }

  Envoy::ProtobufTypes::MessagePtr createEmptyConfigProto() override {
    return Envoy::ProtobufTypes::MessagePtr{new nighthawk::server::TestOrigin()};
  }

  std::string name() override { return "test-origin"; }

private:
  Envoy::Http::FilterFactoryCb createFilter(const nighthawk::server::TestOrigin& proto_config,
                                            Envoy::Server::Configuration::FactoryContext&) {
    Nighthawk::Server::HttpTestOriginDecoderFilterConfigSharedPtr config =
        std::make_shared<Nighthawk::Server::HttpTestOriginDecoderFilterConfig>(
            Nighthawk::Server::HttpTestOriginDecoderFilterConfig(proto_config));

    return [config](Envoy::Http::FilterChainFactoryCallbacks& callbacks) -> void {
      auto filter = new Nighthawk::Server::HttpTestOriginDecoderFilter(config);
      callbacks.addStreamDecoderFilter(Envoy::Http::StreamDecoderFilterSharedPtr{filter});
    };
  }
};

static Envoy::Registry::RegisterFactory<HttpTestOriginDecoderFilterConfig,
                                        Envoy::Server::Configuration::NamedHttpFilterConfigFactory>
    register_;
} // namespace Configuration
} // namespace Server
} // namespace Nighthawk

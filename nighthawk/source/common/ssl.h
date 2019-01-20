
#pragma once

// TODO(oschaaf): this doesn't actually validate certs. FIX!!

#include "server/transport_socket_config_impl.h"

#include "common/ssl/context_config_impl.h"
#include "common/ssl/context_manager_impl.h"
#include "common/ssl/ssl_socket.h"

#include "envoy/network/transport_socket.h"

#include "openssl/ssl.h" // TLS1_2_VERSION etc

namespace Nighthawk {
namespace Ssl {

const std::string DEFAULT_CIPHER_SUITES =
#ifndef BORINGSSL_FIPS
    "[ECDHE-ECDSA-AES128-GCM-SHA256|ECDHE-ECDSA-CHACHA20-POLY1305]:"
    "[ECDHE-RSA-AES128-GCM-SHA256|ECDHE-RSA-CHACHA20-POLY1305]:"
#else // BoringSSL FIPS
    "ECDHE-ECDSA-AES128-GCM-SHA256:"
    "ECDHE-RSA-AES128-GCM-SHA256:"
#endif
    "ECDHE-ECDSA-AES128-SHA:"
    "ECDHE-RSA-AES128-SHA:"
    "AES128-GCM-SHA256:"
    "AES128-SHA:"
    "ECDHE-ECDSA-AES256-GCM-SHA384:"
    "ECDHE-RSA-AES256-GCM-SHA384:"
    "ECDHE-ECDSA-AES256-SHA:"
    "ECDHE-RSA-AES256-SHA:"
    "AES256-GCM-SHA384:"
    "AES256-SHA";

const std::string DEFAULT_ECDH_CURVES =
#ifndef BORINGSSL_FIPS
    "X25519:"
#endif
    "P-256";

namespace {
// This SslSocket will be used when SSL secret is not fetched from SDS server.
class MNotReadySslSocket : public Envoy::Network::TransportSocket {
public:
  // Network::TransportSocket
  void setTransportSocketCallbacks(Envoy::Network::TransportSocketCallbacks&) override {}
  std::string protocol() const override { return Envoy::EMPTY_STRING; }
  bool canFlushClose() override { return true; }
  void closeSocket(Envoy::Network::ConnectionEvent) override {}
  Envoy::Network::IoResult doRead(Envoy::Buffer::Instance&) override {
    return {Envoy::Network::PostIoAction::Close, 0, false};
  }
  Envoy::Network::IoResult doWrite(Envoy::Buffer::Instance&, bool) override {
    return {Envoy::Network::PostIoAction::Close, 0, false};
  }
  void onConnected() override {}
  const Envoy::Ssl::Connection* ssl() const override { return nullptr; }
};

} // namespace

// TODO(oschaaf): make a concrete implementation out of this one.
class MClientContextConfigImpl : public Envoy::Ssl::ClientContextConfig {
public:
  MClientContextConfigImpl(bool h2) : alpn_(h2 ? "h2" : "http/1.1") {}
  ~MClientContextConfigImpl() override = default;

  const std::string& alpnProtocols() const override { return alpn_; };

  const std::string& cipherSuites() const override { return DEFAULT_CIPHER_SUITES; };

  const std::string& ecdhCurves() const override { return DEFAULT_ECDH_CURVES; };

  std::vector<std::reference_wrapper<const Envoy::Ssl::TlsCertificateConfig>>
  tlsCertificates() const override {
    std::vector<std::reference_wrapper<const Envoy::Ssl::TlsCertificateConfig>> configs;
    for (const auto& config : tls_certificate_configs_) {
      configs.emplace_back(config);
    }
    return configs;
  };

  const Envoy::Ssl::CertificateValidationContextConfig*
  certificateValidationContext() const override {
    return validation_context_config_.get();
  };

  unsigned minProtocolVersion() const override { return TLS1_VERSION; };

  unsigned maxProtocolVersion() const override { return TLS1_2_VERSION; };

  bool isReady() const override { return true; };

  void setSecretUpdateCallback(std::function<void()> callback) override { callback_ = callback; };

  // Ssl::ClientContextConfig interface
  const std::string& serverNameIndication() const override { return foo_; };

  bool allowRenegotiation() const override { return true; };

  size_t maxSessionKeys() const override { return 0; };

  const std::string& signingAlgorithmsForTest() const override { return foo_; };

private:
  std::string foo_;
  std::string alpn_;
  std::function<void()> callback_;
  std::vector<Envoy::Ssl::TlsCertificateConfigImpl> tls_certificate_configs_;
  Envoy::Ssl::CertificateValidationContextConfigPtr validation_context_config_;
};

class MClientSslSocketFactory : public Envoy::Network::TransportSocketFactory,
                                public Envoy::Secret::SecretCallbacks,
                                Envoy::Logger::Loggable<Envoy::Logger::Id::config> {
public:
  MClientSslSocketFactory(Envoy::Stats::Store& store, Envoy::TimeSource& time_source, bool h2)
      : config_(h2), scope_(store.createScope(fmt::format("cluster.{}.", "ssl-client"))) {
    Envoy::Ssl::ClientContextSharedPtr context =
        std::make_shared<Envoy::Ssl::ClientContextImpl>(*scope_, config_, time_source);
    ssl_ctx_ = context;
  }

  Envoy::Network::TransportSocketPtr createTransportSocket(
      Envoy::Network::TransportSocketOptionsSharedPtr transport_socket_options) const override {
    Envoy::Ssl::ClientContextSharedPtr ssl_ctx = ssl_ctx_;
    ASSERT(ssl_ctx);
    return std::make_unique<Envoy::Ssl::SslSocket>(
        std::move(ssl_ctx), Envoy::Ssl::InitialState::Client, transport_socket_options);
  }

  bool implementsSecureTransport() const override { return true; };

  // Secret::SecretCallbacks
  void onAddOrUpdateSecret() override { ENVOY_LOG(debug, "onAddOrUpdateSecret() called"); }

private:
  Envoy::Ssl::ClientContextSharedPtr ssl_ctx_;
  MClientContextConfigImpl config_;
  Envoy::Stats::ScopePtr scope_;
};

} // namespace Ssl
} // namespace Nighthawk
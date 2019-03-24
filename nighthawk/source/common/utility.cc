
#include "absl/strings/match.h"
#include "absl/strings/str_split.h"

#include "common/http/utility.h"
#include "common/network/utility.h"

#include "nighthawk/source/common/utility.h"

namespace Nighthawk {

namespace PlatformUtils {

// returns 0 on failure. returns the number of HW CPU's
// that the current thread has affinity with.
// TODO(oschaaf): mull over what to do w/regard to hyperthreading.
uint32_t determineCpuCoresWithAffinity() {
  const pthread_t thread = pthread_self();
  cpu_set_t cpuset;
  int i;

  CPU_ZERO(&cpuset);
  i = pthread_getaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
  if (i == 0) {
    return CPU_COUNT(&cpuset);
  }
  return 0;
}

} // namespace PlatformUtils

size_t Uri::findPortSeparator(absl::string_view hostname) {
  if (hostname.size() > 0 && hostname[0] == '[') {
    return hostname.find(":", hostname.find(']'));
  }
  return hostname.rfind(":");
}

Uri::Uri(absl::string_view uri) : scheme_("http") {
  absl::string_view host, path;
  Envoy::Http::Utility::extractHostPathFromUri(uri, host, path);

  if (host.size() == 0) {
    throw InvalidUriException("Invalid URI (no host)");
  }

  host_and_port_ = std::string(host);
  path_ = std::string(path);
  const bool is_https = absl::StartsWith(uri, "https://");
  const size_t scheme_end = uri.find("://", 0);
  if (scheme_end != std::string::npos) {
    scheme_ = absl::AsciiStrToLower(uri.substr(0, scheme_end));
  }

  const size_t colon_index = findPortSeparator(host_and_port_);

  if (colon_index == absl::string_view::npos) {
    port_ = is_https ? 443 : 80;
    host_without_port_ = host_and_port_;
    host_and_port_ = fmt::format("{}:{}", host_and_port_, port_);
  } else {
    port_ = std::stoi(host_and_port_.substr(colon_index + 1));
    host_without_port_ = host_and_port_.substr(0, colon_index);
  }
}

bool Uri::tryParseHostAsAddress(const Envoy::Network::DnsLookupFamily dns_lookup_family) {
  try {
    address_ = Envoy::Network::Utility::parseInternetAddressAndPort(
        host_and_port_, dns_lookup_family == Envoy::Network::DnsLookupFamily::V6Only);
  } catch (Envoy::EnvoyException) {
    // Could not parsed as a valid address:port
  }
  return address_.get() != nullptr;
}

bool Uri::performDnsLookup(Envoy::Event::Dispatcher& dispatcher,
                           const Envoy::Network::DnsLookupFamily dns_lookup_family) {
  // We couldn't interpret the host as an ip-address, so attempt dns resolution.
  auto dns_resolver = dispatcher.createDnsResolver({});

  Envoy::Network::ActiveDnsQuery* active_dns_query_ = dns_resolver->resolve(
      host_without_port(), dns_lookup_family,
      [this, &dispatcher, &active_dns_query_](
          const std::list<Envoy::Network::Address::InstanceConstSharedPtr>&& address_list) -> void {
        active_dns_query_ = nullptr;
        if (!address_list.empty()) {
          address_ = Envoy::Network::Utility::getAddressWithPort(*address_list.front(), port());
          ENVOY_LOG(debug, "DNS resolution complete for {} ({} entries, using {}).",
                    host_without_port(), address_list.size(), address_->asString());
        }
        dispatcher.exit();
      });

  // Wait for DNS resolution to complete before proceeding.
  dispatcher.run(Envoy::Event::Dispatcher::RunType::Block);
  return address_.get() != nullptr;
}

Envoy::Network::Address::InstanceConstSharedPtr
Uri::resolve(Envoy::Event::Dispatcher& dispatcher,
             const Envoy::Network::DnsLookupFamily dns_lookup_family) {
  if (!needs_resolve_) {
    return address_;
  }

  if (tryParseHostAsAddress(dns_lookup_family) || performDnsLookup(dispatcher, dns_lookup_family)) {
    if ((dns_lookup_family == Envoy::Network::DnsLookupFamily::V6Only &&
         address_->ip()->ipv6() == nullptr) ||
        (dns_lookup_family == Envoy::Network::DnsLookupFamily::V4Only &&
         address_->ip()->ipv4() == nullptr)) {
      ENVOY_LOG(warn, "'{}' resolved to an unsupported address family {}", host_without_port());
      throw InvalidUriException(
          "Could not resolve to an address for the requested address family.");
    }
  } else {
    ENVOY_LOG(warn, "Could not resolve host {}", host_without_port());
    throw InvalidUriException("Could not determine address");
  }

  needs_resolve_ = false;
  return address_;
}

} // namespace Nighthawk
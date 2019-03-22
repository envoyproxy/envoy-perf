
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

size_t Uri::findPortSeparatorInAuthority(absl::string_view authority) {
  size_t colon_index = std::string::npos;
  bool in_ipv6_address = false;
  bool last_seen_dot = true;

  // TODO(oschaaf): We need to revisit this and improve. This performs some
  // limited hostname validation.
  for (size_t i = 0; i < authority.size(); i++) {
    char c = authority[i];
    if (i == 0 && c == '[') {
      in_ipv6_address = true;
    } else if (in_ipv6_address && c == ']') {
      in_ipv6_address = false;
    } else {
      if (!in_ipv6_address && i > 0 && c == ':') {
        colon_index = i;
        break;
      } else if (c == '.') {
        if (last_seen_dot) {
          throw InvalidHostException("Invalid hostname");
        }
        last_seen_dot = true;
        continue;
      } else {
        last_seen_dot = false;
      }

      bool ok = std::isalnum(c) || (i > 0 && c == '-') || (in_ipv6_address && c == ':');

      if (!ok) {
        throw InvalidHostException("Invalid hostname");
      }
    }
  }
  if (in_ipv6_address) {
    throw InvalidHostException("Invalid hostname (missing']')");
  }

  return colon_index;
}

Uri::Uri(absl::string_view uri) : scheme_("http") {
  absl::string_view host, path;
  Envoy::Http::Utility::extractHostPathFromUri(uri, host, path);
  host_and_port_ = std::string(host);
  path_ = std::string(path);
  const bool is_https = absl::StartsWith(uri, "https://");
  const size_t scheme_end = uri.find("://", 0);
  if (scheme_end != std::string::npos) {
    scheme_ = absl::AsciiStrToLower(uri.substr(0, scheme_end));
  }

  size_t colon_index;

  try {
    colon_index = findPortSeparatorInAuthority(host_and_port_);
  } catch (InvalidHostException ex) {
    host_error_ = true;
    return;
  }

  if (colon_index == std::string::npos) {
    port_ = is_https ? 443 : 80;
    host_without_port_ = host_and_port_;
    host_and_port_ = fmt::format("{}:{}", host_and_port_, port_);
  } else {
    port_ = std::stoi(host_and_port_.substr(colon_index + 1));
    host_without_port_ = host_and_port_.substr(0, colon_index);
  }
}

} // namespace Nighthawk
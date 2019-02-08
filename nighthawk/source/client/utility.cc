
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
  uint32_t concurrency = 0;
  int i;
  pthread_t thread = pthread_self();
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  i = pthread_getaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
  if (i != 0) {
    return 0;
  } else {
    for (i = 0; i < CPU_SETSIZE; i++) {
      if (CPU_ISSET(i, &cpuset)) {
        concurrency++;
      }
    }
  }
  return concurrency;
}

} // namespace PlatformUtils

Uri::Uri(std::string uri) : scheme_("http") {
  absl::string_view host, path;
  Envoy::Http::Utility::extractHostPathFromUri(uri, host, path);
  host_and_port_ = std::string(host);
  path_ = std::string(path);

  const size_t colon_index = host_and_port_.find(':');
  is_https_ = absl::StartsWith(uri, "https://");

  size_t scheme_end = uri.find("://", 0);

  if (scheme_end != std::string::npos) {
    scheme_ = absl::AsciiStrToLower(uri.substr(0, scheme_end));
  }

  if (colon_index == std::string::npos) {
    port_ = is_https_ ? 443 : 80;
    host_without_port_ = host_and_port_;
    host_and_port_ = fmt::format("{}:{}", host_and_port_, port_);
  } else {
    const std::string tcp_url = fmt::format("tcp://{}", host_and_port_);
    port_ = Envoy::Network::Utility::portFromTcpUrl(tcp_url);
    host_without_port_ = host_and_port_.substr(0, colon_index);
  }
}

} // namespace Nighthawk
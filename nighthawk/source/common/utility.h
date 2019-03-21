#pragma once

#include <string>

#include "absl/strings/string_view.h"

#include "nighthawk/common/exception.h"

namespace Nighthawk {

namespace PlatformUtils {
uint32_t determineCpuCoresWithAffinity();
}

class InvalidHostException : public NighthawkException {
public:
  InvalidHostException(const std::string& message) : NighthawkException(message) {}
};

class Uri {
public:
  static Uri Parse(std::string uri) { return Uri(uri); }

  const std::string& host_and_port() const { return host_and_port_; }
  const std::string& host_without_port() const { return host_without_port_; }
  const std::string& path() const { return path_; }
  uint64_t port() const { return port_; }
  const std::string& scheme() const { return scheme_; }

  bool isValid() const {
    return !host_error_ && (scheme_ == "http" || scheme_ == "https") &&
           (port_ > 0 && port_ <= 65535);
  }

  /**
   * Finds the position of the port separator in the uri authority component. Throws an
   * InvalidHostException when bad input is provided.
   *
   * @param authority valid "host[:port]" fragment.
   * @return size_t the position of the port separator, or std::string::npos if none was found.
   */
  static size_t findPortSeparatorInAuthority(absl::string_view authority);

private:
  Uri(const std::string& uri);

  // TODO(oschaaf): username, password, etc. But we may want to look at
  // pulling in a mature uri parser.
  std::string host_and_port_;
  std::string host_without_port_;
  std::string path_;
  uint64_t port_;
  std::string scheme_;
  bool host_error_{};
};

} // namespace Nighthawk
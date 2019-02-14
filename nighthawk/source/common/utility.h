#pragma once

#include <string>

namespace Nighthawk {

namespace PlatformUtils {
uint32_t determineCpuCoresWithAffinity();
}

class Uri {
public:
  static Uri Parse(std::string uri) { return Uri(uri); }

  const std::string& host_and_port() const { return host_and_port_; }
  const std::string& host_without_port() const { return host_without_port_; }
  const std::string& path() const { return path_; }
  uint64_t port() const { return port_; }
  const std::string& scheme() const { return scheme_; }

  bool isValid() const {
    return (scheme_ == "http" || scheme_ == "https") && (port_ > 0 && port_ <= 65535);
  }

private:
  Uri(const std::string& uri);

  // TODO(oschaaf): username, password, etc. But we may want to look at
  // pulling in a mature uri parser.
  std::string host_and_port_;
  std::string host_without_port_;
  std::string path_;
  uint64_t port_;
  std::string scheme_;
};

} // namespace Nighthawk
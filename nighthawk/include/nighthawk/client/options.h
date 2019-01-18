#pragma once

#include <chrono>
#include <memory>
#include <string>

#include "envoy/common/pure.h"
#include "source/client/options.pb.h"

namespace Nighthawk {
namespace Client {

typedef std::unique_ptr<nighthawk::client::CommandLineOptions> CommandLineOptionsPtr;

class Options {
public:
  virtual ~Options() {}

  virtual uint64_t requests_per_second() const PURE;
  virtual uint64_t connections() const PURE;
  virtual std::chrono::seconds duration() const PURE;
  virtual std::chrono::seconds timeout() const PURE;
  virtual std::string uri() const PURE;
  virtual bool h2() const PURE;
  virtual std::string concurrency() const PURE;
  virtual std::string verbosity() const PURE;

  virtual CommandLineOptionsPtr toCommandLineOptions() const PURE;
};

typedef std::unique_ptr<Options> OptionsPtr;

} // namespace Client
} // namespace Nighthawk

#include "client/options_impl.h"

#include "tclap/CmdLine.h"

namespace Nighthawk {
namespace Client {

OptionsImpl::OptionsImpl(int argc, const char* const* argv) {
  TCLAP::CmdLine cmd("Nighthawk is a web server benchmarking tool.", ' ', "PoC");

  TCLAP::ValueArg<uint64_t> requests_per_second("", "rps",
                                                "The target requests-per-second rate. Default: 5.",
                                                false, 5 /*default qps*/, "uint64_t", cmd);
  TCLAP::ValueArg<uint64_t> connections("", "connections",
                                        "The number of connections that the test should maximally "
                                        "use. Default: 1.",
                                        false, 1, "uint64_t", cmd);
  TCLAP::ValueArg<uint64_t> duration("", "duration",
                                     "The number of seconds that the test should run. Default: 5.",
                                     false, 5, "uint64_t", cmd);
  TCLAP::ValueArg<uint64_t> timeout(
      "", "timeout",
      "Timeout period in seconds used for both connection timeout and grace period waiting for "
      "lagging responses to come in after the test run is done. Default: 5.",
      false, 5, "uint64_t", cmd);

  TCLAP::SwitchArg h2("", "h2", "Use HTTP/2", cmd);

  TCLAP::ValueArg<std::string> concurrency(
      "", "concurrency",
      "The number of concurrent event loops that should be used. Specify 'auto' to let nighthawk "
      "run leverage all (aligned) vCPUs. Note that increasing this effectively multiplies "
      "configured --rps and --connection values. Default: 1.",
      false, "1", "string", cmd);

  std::vector<std::string> log_levels;
  log_levels.push_back("trace");
  log_levels.push_back("debug");
  log_levels.push_back("info");
  log_levels.push_back("warn");
  log_levels.push_back("error");
  TCLAP::ValuesConstraint<std::string> verbosities_allowed(log_levels);

  TCLAP::ValueArg<std::string> verbosity(
      "v", "verbosity",
      "Verbosity of the output. Possible values: [trace, debug, info, warn, error, critical]. The "
      "default level is 'info'.",
      false, "info", &verbosities_allowed, cmd);

  TCLAP::UnlabeledValueArg<std::string> uri("uri",
                                            "uri to benchmark. http:// and https:// are supported, "
                                            "but in case of https no certificates are validated.",
                                            true, "", "uri format", cmd);

  cmd.setExceptionHandling(false);
  try {
    cmd.parse(argc, argv);
  } catch (TCLAP::ArgException& e) {
    try {
      cmd.getOutput()->failure(cmd, e);
    } catch (const TCLAP::ExitException&) {
      // failure() has already written an informative message to stderr, so all that's left to do
      // is throw our own exception with the original message.
      throw MalformedArgvException(e.what());
    }
  } catch (const TCLAP::ExitException& e) {
    // parse() throws an ExitException with status 0 after printing the output for --help and
    // --version.
    throw NoServingException();
  }

  requests_per_second_ = requests_per_second.getValue();
  connections_ = connections.getValue();
  duration_ = duration.getValue();
  timeout_ = timeout.getValue();
  uri_ = uri.getValue();
  h2_ = h2.getValue();
  concurrency_ = concurrency.getValue();
  verbosity_ = verbosity.getValue();
}

CommandLineOptionsPtr OptionsImpl::toCommandLineOptions() const {
  CommandLineOptionsPtr command_line_options =
      std::make_unique<nighthawk::client::CommandLineOptions>();

  command_line_options->set_connections(connections());
  command_line_options->mutable_duration()->set_seconds(duration().count());
  command_line_options->set_requests_per_second(requests_per_second());
  command_line_options->mutable_duration()->set_seconds(timeout().count());
  command_line_options->set_h2(h2());
  command_line_options->set_uri(uri());
  command_line_options->set_concurrency(concurrency());
  command_line_options->set_verbosity(verbosity());

  return command_line_options;
}

} // namespace Client
} // namespace Nighthawk

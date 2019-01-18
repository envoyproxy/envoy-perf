#pragma once

#include <stdexcept>
#include <string>

namespace Nighthawk {
/**
 * Base class for all nighthawk exceptions.
 */
class NighthawkException : public std::runtime_error {
public:
  NighthawkException(const std::string& message) : std::runtime_error(message) {}
};

// TODO(oschaaf): restructure.
namespace Client {

class NoServingException : public NighthawkException {
public:
  NoServingException() : NighthawkException("NoServingException") {}
};

/**
 * Thrown when an OptionsImpl was not constructed because the argv was invalid.
 */
class MalformedArgvException : public NighthawkException {
public:
  MalformedArgvException(const std::string& what) : NighthawkException(what) {}
};

} // namespace Client

} // namespace Nighthawk

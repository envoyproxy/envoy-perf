#include "absl/debugging/symbolize.h"

#include "nighthawk/common/exception.h"

// NOLINT(namespace-nighthawk)

int main(int, char** argv) {
#ifndef __APPLE__
  // absl::Symbolize mostly works without this, but this improves corner case
  // handling, such as running in a chroot jail.
  absl::InitializeSymbolizer(argv[0]);
#endif
  try {
    printf("%s", "Hello world!");
  } catch (const Nighthawk::Client::NoServingException& e) {
    return EXIT_SUCCESS;
  } catch (const Nighthawk::Client::MalformedArgvException& e) {
    return EXIT_FAILURE;
  } catch (const Nighthawk::NighthawkException& e) {
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}

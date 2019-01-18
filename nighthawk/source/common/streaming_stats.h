#pragma once

#include <cstdint>
#include <math.h>

namespace Nighthawk {

// TODO(oschaaf): test this class.
class StreamingStats {
public:
  StreamingStats();
  void addValue(int64_t value);
  int64_t count() const;
  double mean() const;
  double variance() const;
  double stdev() const;

  StreamingStats combine(const StreamingStats& a);

private:
  int64_t count_;
  double mean_;
  double sum_of_squares_;
};

} // namespace Nighthawk
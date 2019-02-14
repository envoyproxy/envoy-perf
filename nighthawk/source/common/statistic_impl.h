#pragma once

#include <memory>
#include <vector>

#include "nighthawk/hdrhistogram_c/src/hdr_histogram.h"

#include "common/common/logger.h"

#include "nighthawk/common/statistic.h"
#include "nighthawk/source/common/frequency.h"

namespace Nighthawk {

class StatisticImpl : public Statistic, public Envoy::Logger::Loggable<Envoy::Logger::Id::main> {
public:
  void dumpToStdOut(const std::string& header) const override;
  void toProtoOutput(nighthawk::client::Output& output) override;
};

/**
 * Simple statistic that keeps track of count/mean/var/stdev with low memory
 * requirements.
 */
class StreamingStatistic : public StatisticImpl {
public:
  StreamingStatistic();
  void addValue(int64_t value) override;
  uint64_t count() const override;
  double mean() const override;
  double variance() const override;
  double stdev() const override;
  std::unique_ptr<Statistic> combine(const Statistic& a) override;

private:
  uint64_t count_;
  double mean_;
  double sum_of_squares_;
};

/**
 * InMemoryStatistic uses StreamingStatistic under the hood to compute statistics.
 * Stores the raw latencies in-memory, which may accumulate to a lot
 * of data(!). Not used right now, but useful for debugging purposes.
 */
class InMemoryStatistic : public StatisticImpl {
public:
  InMemoryStatistic();
  void addValue(int64_t sample_value) override;
  uint64_t count() const override;
  double mean() const override;
  double variance() const override;
  double stdev() const override;
  std::unique_ptr<Statistic> combine(const Statistic& a) override;

private:
  std::vector<int64_t> samples_;
  std::unique_ptr<Statistic> streaming_stats_;
};

/**
 * HdrStatistic uses HdrHistogram under the hood to compute statistics.
 */
class HdrStatistic : public StatisticImpl {
public:
  HdrStatistic();
  virtual ~HdrStatistic() override;
  void addValue(int64_t sample_value) override;
  uint64_t count() const override;
  double mean() const override;
  double variance() const override;
  double stdev() const override;

  /**
   * HdrStatistic is a little less precise then StreamingStatistics.
   * @returns false when precision is 'high' compared to HdrHistogram.
   * For testing purposes only.
   */
  std::unique_ptr<Statistic> combine(const Statistic& a) override;

  /**
   * Gets a HdrStatistic instance with corrections for coordinated omission applied.
   * This should be done only once.
   * @param frequency The frequency at which latencies ought to have been measured.
   * NOTE: this is neither used nor tested at the moment.
   * @returns HdrStatistic unique_ptr.
   */
  std::unique_ptr<HdrStatistic> getCorrected(const Frequency& frequency);
  void dumpToStdOut(const std::string& header) const override;
  void toProtoOutput(nighthawk::client::Output& output) override;
  virtual uint64_t significant_digits() const override { return SIGNIFICANT_DIGITS; }

private:
  static const int SIGNIFICANT_DIGITS;
  struct hdr_histogram* histogram_;
};

} // namespace Nighthawk
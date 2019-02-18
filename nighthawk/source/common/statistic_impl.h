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
  std::string toString() const override;
  nighthawk::client::Statistic toProto() override;
};

/**
 * Simple statistic that keeps track of count/mean/pvariance/pstdev with low memory
 * requirements, but the potential for errors due to catastrophic cancellation.
 */
class SimpleStatistic : public StatisticImpl {
public:
  SimpleStatistic();
  void addValue(int64_t value) override;
  uint64_t count() const override;
  double mean() const override;
  double pvariance() const override;
  double pstdev() const override;
  std::unique_ptr<Statistic> combine(const Statistic& statistic) override;

private:
  uint64_t count_;
  double sum_x_;
  double sum_x2_;
};

/**
 * Simple statistic that keeps track of count/mean/pvariance/pstdev with low memory
 * requirements.
 */
class StreamingStatistic : public StatisticImpl {
public:
  StreamingStatistic();
  void addValue(int64_t value) override;
  uint64_t count() const override;
  double mean() const override;
  double pvariance() const override;
  double pstdev() const override;
  std::unique_ptr<Statistic> combine(const Statistic& statistic) override;
  bool resistsCatastrophicCancellation() const override { return true; }

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
  double pvariance() const override;
  double pstdev() const override;
  std::unique_ptr<Statistic> combine(const Statistic& statistic) override;
  bool resistsCatastrophicCancellation() const override {
    return streaming_stats_->resistsCatastrophicCancellation();
  }

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
  double pvariance() const override;
  double pstdev() const override;

  std::unique_ptr<Statistic> combine(const Statistic& statistic) override;
  std::string toString() const override;
  nighthawk::client::Statistic toProto() override;
  virtual uint64_t significantDigits() const override { return SignificantDigits; }

private:
  static const int SignificantDigits;
  struct hdr_histogram* histogram_;
};

} // namespace Nighthawk
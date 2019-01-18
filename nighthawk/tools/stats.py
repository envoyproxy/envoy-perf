#!/usr/bin/env python3

import sys
import statistics

from hdrh.histogram import HdrHistogram
import jsonpickle
import json

histogram = HdrHistogram(1, 60000000, 4)


def pp(histogram, p):
    v = histogram.get_value_at_percentile(p)
    print("p{}: {}".format(p, v))


def print_latencies(histogram, content):
    print("Uncorrected hdr histogram percentiles (us)")
    pp(histogram, 50)
    pp(histogram, 75)
    pp(histogram, 90)
    pp(histogram, 99)
    pp(histogram, 99.9)
    pp(histogram, 99.99)
    pp(histogram, 99.999)
    pp(histogram, 100)

    print("min:", min(content))
    print("max:", max(content))
    print("mean:", statistics.mean(content))
    print("median:", statistics.median(content))
    print("var:", statistics.variance(content))
    print("stdev:", statistics.stdev(content))


def get_latencies(path, type):
    content = []
    with open(path) as f:
        content = f.readlines()
    if type == "envoy":
        content = [int(json.loads(x)["duration"]) / 1000 for x in content[1:]]
    elif type == "benchmark":
        content = [int(x.strip()) for x in content]

    return content


def main():
    content = get_latencies(sys.argv[1], sys.argv[2])
    for idx, n in enumerate(content):
        content[idx] = float(n) / 1000
    for n in content:
        histogram.record_value(n)

    print_latencies(histogram, content)


main()

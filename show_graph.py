"""This file creates a graph from the metric Gcloud SQL database."""

import argparse

import database_helpers as db_utils
import matplotlib.pyplot as plt
import MySQLdb
import numpy as np
import shell_helpers as sh_utils
import utils


def DrawBarGraph(connection, table_name, y_axis_field, x_axis_values,
                 x_axis_field):
  """This function draws a single graph based on the mean value.

  Args:
    connection: the connection to get data from the databade
    table_name: the name of the table to get data from
    y_axis_field: column name in the table for the y axis
    x_axis_values: the values in x axis to compare
    x_axis_field: column name in the table for the x axis
  """
  direct_lists = list()
  envoy_lists = list()

  for x in x_axis_values:
    condition = ("where {}=\"{}\" and"
                 " category=\"direct\"").format(x_axis_field, x)
    direct_list = db_utils.SingleColumnToList(db_utils.GetFieldFromTable(
        connection, table_name, field=y_axis_field, cond=condition))
    if not direct_list:
      print "{} {} is not found in table for direct results.".format(
          x_axis_field, x)
      direct_list = [0]

    direct_lists.append(direct_list)

    condition = ("where {}=\"{}\" and"
                 " category=\"envoy\"").format(x_axis_field, x)
    envoy_list = db_utils.SingleColumnToList(db_utils.GetFieldFromTable(
        connection, table_name, field=y_axis_field, cond=condition))
    if not envoy_list:
      print "{} {} is not found in table for Envoy results.".format(
          x_axis_field, x)
      envoy_list = [0]

    envoy_lists.append(envoy_list)

  ind = np.arange(len(x_axis_values))
  direct_means = list()
  direct_std = list()
  envoy_means = list()
  envoy_std = list()

  for single_set in direct_lists:
    direct_means.append(np.mean(single_set))
    direct_std.append(np.std(single_set))
  for single_set in envoy_lists:
    envoy_means.append(np.mean(single_set))
    envoy_std.append(np.std(single_set))

  width = 0.35
  fig, ax = plt.subplots()
  rects1 = ax.bar(ind, direct_means, width, color="r", yerr=direct_std)
  rects2 = ax.bar(ind + width, envoy_means, width, color="y", yerr=envoy_std)

  ax.set_ylabel(y_axis_field)
  ax.set_xlabel(x_axis_field)
  ax.set_xticks(ind + width)
  ax.set_xticklabels(x_axis_values)
  ax.legend((rects1[0], rects2[0]), ("Direct", "Envoy"))
  AutoLabel(rects1, ax)
  AutoLabel(rects2, ax)
  fig.savefig("{} {}.pdf".format(
      x_axis_field, ",".join(str(i) for i in x_axis_values)),
              bbox_inches="tight")


def AutoLabel(rects, ax):
  """Attach a text label above each bar displaying its height.

  This function is taken from matplotlib Demo.
  Args:
    rects: the rectangle
    ax: the axis
  """
  for rect in rects:
    height = rect.get_height()
    ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
            "%d " % int(height),
            ha="center", va="bottom")


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--db_instance_name",
                      help="the name of the gcloud instance",
                      default="envoy-db-instance")
  parser.add_argument("--username", help="username on the host DB",
                      default="root")
  parser.add_argument("--database", help="name of the database",
                      default="envoy_stat_db")
  parser.add_argument("--table_name", help=("the table which stores "
                                            "the benchmarking data"),
                      default="envoy_stat")
  parser.add_argument("--project",
                      help="the project name in Google Cloud.",
                      default="envoy-ci")
  parser.add_argument("--logfile",
                      help="the local log file for this script. New log will be"
                           "appended to this file.", default="benchmark.log")
  parser.add_argument("--envoy_hashes",
                      help="the hash of envoy version",
                      nargs="+")
  parser.add_argument("--runids",
                      help=("the run ids to be plotted on the graph."
                            " Give in a space-separated format."),
                      nargs="+")
  parser.add_argument("--fieldname",
                      help="the name of the field for which you want the graph",
                      default="total_req_per_sec")

  args = parser.parse_args()
  logfile = open(args.logfile, "ab")
  hostname = db_utils.GetInstanceIP(args.db_instance_name, args.project)

  password = utils.GetRandomPassword()
  sh_utils.RunGCloudService(["users", "set-password", args.username, "%",
                             "--instance", args.db_instance_name, "--password",
                             password], project=args.project,
                            service="sql", logfile=logfile)
  print "DB Usernames and passwords are set."
  connection = MySQLdb.connect(host=hostname, user=args.username,
                               passwd=password, db=args.database)
  print "Connection to get data from DB is successful."

  if args.runids:
    DrawBarGraph(connection, args.table_name, args.fieldname,
                 args.runids, "runid")
  if args.envoy_hashes:
    DrawBarGraph(connection, args.table_name, args.fieldname,
                 args.envoy_hashes, "envoy_hash")


if __name__ == "__main__":
  main()

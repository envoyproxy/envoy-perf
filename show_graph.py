"""This file creates a graph for some metric in the Gcloud SQL database."""

import argparse

import database_helpers as db_utils
import matplotlib.pyplot as plt
import numpy as np


class ShowGraphError(Exception):
  pass


def DrawBarGraph(connection, table_name, y_axis_field, x_axis_values,
                 x_axis_field, arrangement):
  """This function draws a single graph based on the mean value.

  Args:
    connection: the connection to get data from the database
    table_name: the name of the table to get data from
    y_axis_field: column name in the table for the y axis
    x_axis_values: the values in x axis to compare
    x_axis_field: column name in the table for the x axis
    arrangement: the type of arrangement in the experiment
  """

  def GetListsFromDB(x_axis_values, x_axis_field, connection,
                     table_name, y_axis_field, category):
    """This function returns lists of values of a field from the DB.

    The function returns lists of `y_axis_field` for the values corresponding to
    the `x_axis_values` in `x_axis_field`.
    Args:
      x_axis_values: a list of values for which the `y_axis_field` will be
       fetched for.
      x_axis_field: name of the field for x_axis
      connection: the connection to the database
      table_name: name of the table in the database which has the data
      y_axis_field: the name of the column in the table, whose data will be put
      into the list
      category: Direct or Envoy or which category the data belong to
    Returns:
      Returns a list of lists with all the values of `y_axis_field`
      corresponding to `x_axis_values`.
    """
    lists = list()
    for x in x_axis_values:
      condition = ("where {}=\"{}\" and"
                   " category=\"{}\"").format(x_axis_field, x, category)
      single_list = db_utils.SingleColumnToList(db_utils.GetFieldFromTable(
          connection, table_name, field=y_axis_field, cond=condition))
      if not single_list:
        print "{} {} is not found in table for {} results.".format(
            x_axis_field, x, category)
        single_list = [0]

      lists.append(single_list)
    return lists

  direct_lists = GetListsFromDB(x_axis_values, x_axis_field, connection,
                                table_name, y_axis_field,
                                "direct-{}".format(arrangement))
  envoy_lists = GetListsFromDB(x_axis_values, x_axis_field, connection,
                               table_name, y_axis_field,
                               "envoy-{}".format(arrangement))

  def GetMeansAndStdsFromList(lists):
    """This function returns the means and standard deviation of lists.

    Args:
      lists: A list of lists. Each list inside the top-level list consists
      of a sample for a given variable that summary stats will be computed on.
    Returns:
      A pair of list containing means and standard deviations.
    """
    means = [np.mean(single_list) for single_list in lists]
    stds = [np.std(single_list) for single_list in lists]
    return means, stds

  direct_means, direct_std = GetMeansAndStdsFromList(direct_lists)
  envoy_means, envoy_std = GetMeansAndStdsFromList(envoy_lists)

  ind = np.arange(len(x_axis_values))
  width = 0.35
  fig, ax = plt.subplots()
  rects1 = ax.bar(ind, direct_means, width, color="r", yerr=direct_std)
  rects2 = ax.bar(ind + width, envoy_means, width, color="y", yerr=envoy_std)

  ax.set_ylabel(y_axis_field)
  ax.set_xlabel(x_axis_field)
  ax.set_xticks(ind + width)
  ax.set_xticklabels(x_axis_values, rotation="vertical", fontsize=8)
  # legend will be placed out of the main graph
  ax.legend((rects1[0], rects2[0]), ("Direct", "Envoy"),
            loc="center left", bbox_to_anchor=(1, 0.5))
  AutoLabel(rects1, ax)
  AutoLabel(rects2, ax)
  fig.savefig("{} {} {}.png".format(
      x_axis_field, ",".join(str(i) for i in x_axis_values), y_axis_field),
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


def DrawTimeSeriesGraph(connection, table_name, y_axis_field, time,
                        arrangement):
  """This function draws a time-series graph.

  Args:
    connection: the connection to get data from the database
    table_name: the name of the table to get data from
    y_axis_field: column name in the table for the y axis
    time: the starting time for the graph
    arrangement: the type of arrangement in the experiment
  Raises:
    ShowGraphError: When direct or Envoy's data is not found in the database
  """
  def GetListFromDB(time, category, y_axis_field, connection, table_name):
    condition = ("where time_of_entry >= \"{}\" and"
                 " category=\"{}\" Group By RunID "
                 "Order By time_of_entry").format(
                     time, category)
    single_list = db_utils.GetFieldFromTable(
        connection, table_name,
        field="AVG({}), STDDEV({}), time_of_entry, RunID".format(
            y_axis_field, y_axis_field),
        cond=condition)
    if not single_list:
      print "Values are not found in table for category {}.".format(
          category)
      return None

    return single_list

  direct_list = GetListFromDB(time, "direct-{}".format(arrangement),
                              y_axis_field, connection, table_name)
  envoy_list = GetListFromDB(time, "envoy-{}".format(arrangement),
                             y_axis_field, connection, table_name)

  if direct_list:
    direct_means, direct_std = zip(*direct_list)
    direct_times = [v[2].time().strftime("%H:%M") if not i % 2 else ""
                    for i, v in enumerate(direct_list)]
  else:
    raise ShowGraphError("Direct's data not found for time-series graph.")

  if envoy_list:
    envoy_means, envoy_std = zip(*envoy_list)
    # time is not needed again but if needed, it can be taken from here
    # envoy_times = [v[2] for v in envoy_list]
  else:
    raise ShowGraphError("Envoy's data not found for time-series graph.")

  ind = np.arange(len(direct_times))
  fig, ax = plt.subplots()
  rects1 = ax.errorbar(ind, direct_means, color="r", yerr=direct_std)
  rects2 = ax.errorbar(ind, envoy_means, color="y", yerr=envoy_std)

  ax.set_ylabel(y_axis_field)
  ax.set_xlabel("time")
  ax.set_xticks(ind)
  ax.set_xticklabels(direct_times, rotation="vertical", fontsize=8)
  ax.legend((rects1[0], rects2[0]), ("Direct", "Envoy"),
            loc="center left", bbox_to_anchor=(1, 0.5))
  fig.savefig("Time-{}-{}-{}.png".format(time, arrangement, y_axis_field),
              bbox_inches="tight")


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
  parser.add_argument("--arrangement", help=("the type of arrangement in"
                                             " this experiment."),
                      default="single-vm")
  parser.add_argument("--time", help=("provide the starting time for the "
                                      "time-series graph."),
                      default=None)

  args = parser.parse_args()
  logfile = open(args.logfile, "ab")
  connection = db_utils.AuthorizeMachineAndConnectDB(
      args.db_instance_name, args.project, args.username,
      args.database, logfile)
  print "Connection to get data from DB is successful."

  if args.runids:
    DrawBarGraph(connection, args.table_name, args.fieldname,
                 args.runids, "runid", args.arrangement)
  if args.envoy_hashes:
    DrawBarGraph(connection, args.table_name, args.fieldname,
                 args.envoy_hashes, "envoy_hash", args.arrangement)

  if args.time:
    DrawTimeSeriesGraph(connection, args.table_name, args.fieldname,
                        args.time, args.arrangement)

if __name__ == "__main__":
  main()

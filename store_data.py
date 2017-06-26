"""This file creates is for the DB-related work on the statistics."""

import argparse
import json
import re
import subprocess

import database_helpers as db_utils
import MySQLdb
import pexpect
import python_helpers as python_utils
import shell_helpers as sh_utils


class DataStoreError(Exception):
  pass


def CreateTable(connection, table_name):
  """This function creates the envoy_stat table on the give `connection`.

  Args:
    connection: the connection which will refer to a database in which the table
    will be created.
    table_name: the name of the table to be created.
  Returns/Yields:
    It creates a table on the `connection`.
  """
  create_table_statement = ("CREATE TABLE IF NOT EXISTS  {}"
                            "(id INTEGER NOT NULL AUTO_INCREMENT,"
                            "category VARCHAR(20) NOT NULL,"
                            "time_of_entry DATETIME,"
                            "runid VARCHAR(30),"
                            "envoy_hash VARCHAR(40),"
                            "total_time INTEGER UNSIGNED,"
                            "time_for_1st_byte_max INTEGER UNSIGNED,"
                            "time_for_1st_byte_min INTEGER UNSIGNED,"
                            "time_for_1st_byte_mean INTEGER UNSIGNED,"
                            "time_for_1st_byte_sd INTEGER UNSIGNED,"
                            "time_for_1st_byte_sd_percent FLOAT UNSIGNED,"
                            "requests_success BIGINT UNSIGNED,"
                            "requests_started BIGINT UNSIGNED,"
                            "requests_done BIGINT UNSIGNED,"
                            "requests_timeout BIGINT UNSIGNED,"
                            "requests_error BIGINT UNSIGNED,"
                            "requests_fail BIGINT UNSIGNED,"
                            "requests_total BIGINT UNSIGNED,"
                            "total_data_BPS DOUBLE UNSIGNED,"
                            "time_for_connect_max INTEGER UNSIGNED,"
                            "time_for_connect_min INTEGER UNSIGNED,"
                            "time_for_connect_mean INTEGER UNSIGNED,"
                            "time_for_connect_sd INTEGER UNSIGNED,"
                            "time_for_connect_sd_percent FLOAT UNSIGNED,"
                            "req_per_sec_max INTEGER UNSIGNED,"
                            "req_per_sec_min INTEGER UNSIGNED,"
                            "req_per_sec_mean INTEGER UNSIGNED,"
                            "req_per_sec_sd INTEGER UNSIGNED,"
                            "req_per_sec_sd_percent FLOAT UNSIGNED,"
                            "total_req_per_sec DOUBLE UNSIGNED,"
                            "time_for_request_max INTEGER UNSIGNED,"
                            "time_for_request_min INTEGER UNSIGNED,"
                            "time_for_request_mean INTEGER UNSIGNED,"
                            "time_for_request_sd INTEGER UNSIGNED,"
                            "time_for_request_sd_percent FLOAT UNSIGNED,"
                            "status_codes_2xx BIGINT UNSIGNED,"
                            "status_codes_3xx BIGINT UNSIGNED,"
                            "status_codes_4xx BIGINT UNSIGNED,"
                            "status_codes_5xx BIGINT UNSIGNED,"
                            "traffic_total_bytes BIGINT UNSIGNED,"
                            "traffic_total_data_bytes BIGINT UNSIGNED,"
                            "traffic_total_headers_bytes BIGINT UNSIGNED,"
                            "traffic_total_savings FLOAT UNSIGNED,"
                            "PRIMARY KEY (id)"
                            ")")
  db_utils.ExecuteAndReturnResult(connection,
                                  create_table_statement.format(table_name))


def GetMicrosecondData(data):
  """The function accepts a dictionary and returns microsecond data inside it.

  Based on the unit (s, ms, us) inside the dictionary, the function converts to
  microsecond value.
  Args:
    data: data is a dictionary of the format: {data: <val>, unit: <unit>}.
  Returns:
    A float value on the microsecond unit.
  """
  assert data["unit"] == "us" or data["unit"] == "ms" or data["unit"] == "s"

  if data["unit"] == "us":
    return float(data["data"])
  elif data["unit"] == "ms":
    return float(data["data"]) * 1000
  elif data["unit"] == "s":
    return float(data["data"]) * 1000000


def GetByteData(data):
  """The function accepts a dictionary and returns Bytes value inside it.

  Based on the unit (B, MB, KB), the function converts to Bytes value. It also
  works for B/s, MB/s, etc.
  Args:
    data: data is a dictionary of the format: {data: <val>, unit: <unit>}.
  Returns:
    A float value of the Bytes unit.
  """
  assert (data["unit"].startswith("B") or data["unit"].startswith("K") or
          data["unit"].startswith("M"))

  if data["unit"].startswith("B"):
    return int(data["data"])
  elif data["unit"].startswith("K"):
    return int(float(data["data"]) * 1024)
  elif data["unit"].startswith("M"):
    return int(float(data["data"]) * 1024 * 1024)


def JSONToInsertCommand(table, **kwargs):
  keys = ", ".join(kwargs.keys())
  values = ", ".join("%s" % val for val in kwargs.values())
  command = "INSERT INTO {} ({}) VALUES ({});".format(table, keys, values)
  return command

def Enquote(string):
  """This function adds quotations around the string.

  Args:
    string: input string
  Returns:
    A string with a starting and ending quote.
  """
  return "\"{}\"".format(string)


def InsertIntoTable(connection, table, json_file, runid, envoy_hash):
  """The function inserts h2load result in JSON file into the provided table.

  The function takes an opened JSON filestream, loads the JSON structure inside
  it and inserts h2load statistical values into the table provided. The table
  should have same columns, corresponding to the metrics of the h2load result,
  written into the JSON file. It's tightly bounded with the JSON file format
  and the table-structure.
  Args:
    connection: the connection with the database
    table: name of the table in which `json_file` will be entered into
    json_file: an opened filestream in reading mode. The file needs to be in
    the correct JSON format, generated by the benchmarking script.
  Returns/Yields:
    It inserts the json_file into the `table`, by iterating the file.
  """
  whole_data = json.load(json_file)

  # first, there will be a number of categories
  for (key, val) in whole_data.iteritems():
    # for each category there will be a number of benchkarking reading
    # print key
    for row in val:
      # TODO(sohamcodes): We need to think of a way to do the below more
      # gracefully, probably by keeping consistency in the JSON format and
      # DB table column-names
      command = JSONToInsertCommand(
          table, category=Enquote(key),
          total_time=GetMicrosecondData(row["total_time"]),
          time_for_1st_byte_max=GetMicrosecondData(
              row["time_for_1st_byte"]["max"]),
          time_for_1st_byte_min=GetMicrosecondData(
              row["time_for_1st_byte"]["min"]),
          time_for_1st_byte_mean=GetMicrosecondData(
              row["time_for_1st_byte"]["mean"]),
          time_for_1st_byte_sd=GetMicrosecondData(
              row["time_for_1st_byte"]["sd"]),
          time_for_1st_byte_sd_percent=float(
              row["time_for_1st_byte"]["sd%"]),
          requests_success=int(row["requests_statistics"]["success"]),
          requests_started=int(row["requests_statistics"]["started"]),
          requests_done=int(row["requests_statistics"]["done"]),
          requests_timeout=int(row["requests_statistics"]["timeout"]),
          requests_error=int(row["requests_statistics"]["error"]),
          requests_fail=int(row["requests_statistics"]["fail"]),
          requests_total=int(row["requests_statistics"]["total"]),
          total_data_BPS=GetByteData(row["total_data_per_sec"]),
          time_for_connect_max=GetMicrosecondData(
              row["time_for_connect"]["max"]),
          time_for_connect_min=GetMicrosecondData(
              row["time_for_connect"]["min"]),
          time_for_connect_mean=GetMicrosecondData(
              row["time_for_connect"]["mean"]),
          time_for_connect_sd=GetMicrosecondData(
              row["time_for_connect"]["sd"]),
          time_for_connect_sd_percent=float(row["time_for_connect"]["sd%"]),
          req_per_sec_max=float(row["req/s"]["max"]),
          req_per_sec_min=float(row["req/s"]["min"]),
          req_per_sec_mean=float(row["req/s"]["mean"]),
          req_per_sec_sd=float(row["req/s"]["sd"]),
          req_per_sec_sd_percent=float(row["req/s"]["sd%"]),
          total_req_per_sec=float(row["total_req_per_sec"]["data"]),
          time_for_request_max=GetMicrosecondData(
              row["time_for_request"]["max"]),
          time_for_request_min=GetMicrosecondData(
              row["time_for_request"]["min"]),
          time_for_request_mean=GetMicrosecondData(
              row["time_for_request"]["mean"]),
          time_for_request_sd=GetMicrosecondData(
              row["time_for_request"]["sd"]),
          time_for_request_sd_percent=float(row["time_for_request"]["sd%"]),
          status_codes_2xx=int(row["status_codes_statistics"]["2xx"]),
          status_codes_3xx=int(row["status_codes_statistics"]["3xx"]),
          status_codes_4xx=int(row["status_codes_statistics"]["4xx"]),
          status_codes_5xx=int(row["status_codes_statistics"]["5xx"]),
          traffic_total_bytes=int(row["traffic_details"]["traffic_total"]),
          traffic_total_data_bytes=int(
              row["traffic_details"]["traffic_data"]),
          traffic_total_headers_bytes=int(
              row["traffic_details"]["traffic_headers"]),
          traffic_total_savings=float(
              row["traffic_details"]["traffic_savings%"]),
          runid=Enquote(runid),
          envoy_hash=Enquote(envoy_hash),
          time_of_entry="NOW()"
          )
      db_utils.ExecuteAndReturnResult(connection, command)


def GetInstanceIP(instance_name, project):
  """This function gets a SQL instance's IP by running the gcloud sql describe.

  Args:
    instance_name: name of the instance
    project: the project name in which the instance is in
  Returns:
    Returns a string which is the IP Address of the `instance_name`.
  """
  status = subprocess.check_output(
      sh_utils.GetGcloud(["instances", "describe", instance_name],
                         project=project, service="sql"))
  ip = re.search(r"ipAddress:\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", status)
  return ip.group(1)


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("--db_instance_name",
                      help="the name of the gcloud instance",
                      default="envoy-db-instance")
  parser.add_argument("--tier", help="the tier of GCloud SQL service",
                      default="db-n1-standard-2")
  parser.add_argument("--username", help="username on the host DB",
                      default="root")
  parser.add_argument("--password",
                      help="password for the username on the host DB",
                      default="password")
  parser.add_argument("--database", help="name of the database",
                      default="envoy_stat_db")
  parser.add_argument("--json_result", help="the JSON result file",
                      default="result.json")
  parser.add_argument("--table_name", help=("the table which stores "
                                            "the benchmarking data"),
                      default="envoy_stat")
  parser.add_argument("--project",
                      help="the project name in Google Cloud.",
                      default="envoy-ci")
  parser.add_argument("--logfile",
                      help="the local log file for this script. New log will be"
                           "appended to this file.", default="benchmark.log")
  parser.add_argument("--ownip", help=("the machine's IP from where"
                                       " the script is being run"),
                      default="127.0.0.1")
  parser.add_argument("--envoy_hash",
                      help="the hash of envoy version",
                      default="xxxxxx")
  parser.add_argument("--runid",
                      help="the run id of this benchmark",
                      default="0")

  python_utils.CreateMutuallyExclusiveArgument(parser, "create_instance",
                                               ("turn on if you want to create"
                                                " a Google Cloud SQL instance"))
  parser.set_defaults(create_instance=True)

  python_utils.CreateMutuallyExclusiveArgument(parser, "create_db",
                                               ("turn on if you want"
                                                " to create the DB"))
  parser.set_defaults(create_db=True)

  python_utils.CreateMutuallyExclusiveArgument(parser, "delete_db",
                                               ("turn on if you want"
                                                " to delete the DB"))
  parser.set_defaults(delete_db=True)

  args = parser.parse_args()
  logfile = open(args.logfile, "ab")

  if args.create_instance:
    sh_utils.RunGCloudService(["instances", "create", args.db_instance_name,
                               "--tier", args.tier], args.project,
                              "sql", logfile)
    print "Google Cloud SQL Instance {} is created.".format(
        args.db_instance_name)
  else:
    print "Instance creation is skipped due to --no-create_instance."

  sh_utils.RunGCloudService(["users", "set-password", args.username, "%",
                             "--instance", args.db_instance_name, "--password",
                             args.password], project=args.project,
                            service="sql", logfile=logfile)
  print "Usernames and passwords are set."

  auth_ip_command = sh_utils.GetGcloud(
      ["instances", "patch", args.db_instance_name,
       "--authorized-networks", args.ownip],
      project=args.project, service="sql")
  auth_ip_command = " ".join(auth_ip_command)
  pexpect.run(auth_ip_command,
              events={"Do you want to continue (Y/n)?": "Y\n"},
              logfile=logfile, timeout=None)
  print ("This machine is configured to use the Google"
         " Cloud SQL Instance {}.").format(args.db_instance_name)

  hostname = GetInstanceIP(args.db_instance_name, args.project)

  if args.create_db:
    connection = MySQLdb.connect(host=hostname, user=args.username,
                                 passwd=args.password)
    print "Connection successful."
    db_utils.ExecuteAndReturnResult(connection, "CREATE DATABASE {};".format(
        args.database))
    connection.select_db(args.database)
    print "Created DB."
  else:
    connection = MySQLdb.connect(host=hostname, user=args.username,
                                 passwd=args.password, db=args.database)
    print "Connection to DB {} is successful.".format(args.database)

  # table will only be created if not exists
  CreateTable(connection, args.table_name)
  with open(args.json_result, "r") as f:
    InsertIntoTable(connection, args.table_name, f, args.runid, args.envoy_hash)
    connection.commit()
    print "Data is inserted from JSON file to Database."

  if args.delete_db:
    db_utils.ExecuteAndReturnResult(connection,
                                    "DROP DATABASE {};".format(args.database))
    print "Database deletion is successful."
  else:
    print "Database deletion is skipped due to --no-delete_db."

  connection.close()
  print "DB Connection closed."

if __name__ == "__main__":
  main()

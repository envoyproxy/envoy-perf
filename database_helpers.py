"""This file consists of database helper functions."""

import re
import subprocess

import MySQLdb
import shell_helpers as sh_utils
import utils


def ExecuteAndReturnResult(connection, statement):
  """This function will execute a SQL statement and return the SQL output.

  Args:
    connection: connection to the DB instance
    statement: statement to be executed.
  Returns:
    It returns the SQL output after executing the `statement`.
  """
  cursor = connection.cursor()
  cursor.execute(statement)
  return cursor.fetchall()


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


def GetFieldFromTable(connection, table_name, field="*", cond=None):
  """This function gets column(s) from a table.

  Args:
    connection: connection to the DB instance
    table_name: name of the table to get the rows from
    field: optional column name(s). default: all the fileds (*)
    cond: optional filters
  Returns:
    Returns all the fields
  """
  statement = "SELECT {} FROM {}".format(field, table_name)
  if cond:
    statement = "{} {}".format(statement, cond)
  statement = "{};".format(statement)
  return ExecuteAndReturnResult(connection, statement)


def SingleColumnToList(select_based_list):
  """This function converts a single-column returned by SELECT to a Python list.

  Args:
    select_based_list: the select based list.
  Returns:
    A Python list
  """
  return [d[0] for d in select_based_list]


def AuthorizeMachineAndConnectDB(db_instance_name, project, username, database,
                                 logfile):
  """This function authorizes a machine to connect to a DB.

  Args:
    db_instance_name: name of the DB instance.
    project: name of the project in which the db_instance belongs to.
    username: username that will be used to log in to the DB
    database: name of the database to connect to
    logfile: logfile for the gcloud command in shell
  Returns:
    Returns the connection after being connected to the DB.
  """
  hostname = GetInstanceIP(db_instance_name, project)

  password = utils.GetRandomPassword()
  sh_utils.RunGCloudService(["users", "set-password", username, "%",
                             "--instance", db_instance_name, "--password",
                             password], project=project,
                            service="sql", logfile=logfile)
  print "DB Usernames and passwords are set."
  connection = MySQLdb.connect(host=hostname, user=username,
                               passwd=password, db=database)
  return connection

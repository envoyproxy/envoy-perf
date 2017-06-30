"""This file consists of database helper functions."""

import re
import subprocess

import shell_helpers as sh_utils


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
  converted_list = list()
  for data in select_based_list:
    converted_list.append(data[0])
  return converted_list

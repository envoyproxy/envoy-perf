"""This file consists of database helper functions."""


def ExecuteAndReturnResult(connection, statement):
  """This function will execute a SQL statement and return the SQL output.

  Args:
    connection: connection to the DB instance
    statement: statement to be executed.
  Returns:
    It returns the SQl output after executing the `statement`.
  """
  cursor = connection.cursor()
  cursor.execute(statement)
  return cursor.fetchall()

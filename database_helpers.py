import MySQLdb

def ExecuteAndReturnResult(connection, statement):
  cursor = connection.cursor()
  cursor.execute(statement)
  return cursor.fetchall()

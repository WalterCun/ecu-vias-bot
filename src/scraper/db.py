""" src/scraper/db.py """
# import sqlite3
# from sqlite3 import Error
#
# import pandas as pd
#
# from src.settings import settings
# from src.patterns.singlenton import SingletonMeta
#
#
# class Database(metaclass=SingletonMeta):
#     """
#     class Database (metaclass=SingletonMeta):
#
#     def __init__(self, database_path=settings.DATABASE_URL):
#         self.connection = None
#         self.create_connection(database_path)
#
#     def create_connection(self, db_file):
#         Establishes a connection to the specified SQLite database file.
#
#         Parameters:
#         db_file (str): The path to the SQLite database file.
#
#         Returns:
#         None
#         """
#     def __init__(self, database_path=settings.DATABASE_URL):
#         self.connection = None
#         self.create_connection(database_path)
#
#     def create_connection(self, db_file):
#         """
#         Creates a connection to the specified SQLite database.
#
#         Parameters:
#         db_file (str): The filepath to the SQLite database.
#
#         Raises:
#         Error: If an error occurs while trying to connect to the database.
#         """
#         try:
#             self.connection = sqlite3.connect(db_file)
#         except Error as e:
#             print(e)
#
#     def exec_query(self, query, params=()):
#         """
#         Executes a given SQL query with optional parameters.
#
#         Parameters:
#         query (str): The SQL query to be executed.
#         params (tuple, optional): The substitution parameters to pass with the query.
#         Default to an empty tuple.
#
#         Returns:
#         None
#         """
#         cursor = self.connection.cursor()
#         cursor.execute(query, params)
#
#     def fetch_all(self, table, where=None, params=()):
#         """
#         Fetches all records from the specified table and returns them as a DataFrame.
#
#         Parameters:
#         table (str): The name of the table to query.
#         where (str, optional): SQL WHERE clause to filter the results.
#         Defaults to None.
#         params (tuple, optional): Parameters to include in the query for SQL injection prevention.
#         Default to an empty tuple.
#
#         Returns:
#         DataFrame: A DataFrame containing the records fetched from the table.
#         """
#         # cursor = self.connection.cursor()
#         query = f'SELECT * FROM {table}'
#
#         if where is not None:
#             query += f' WHERE {where}'
#         #
#         # try:
#
#         df = pd.read_sql_query(query, self.connection, params=params)
#
#         #     cursor.execute(query, params)
#         # except Error as e:
#         #     return []
#         return df
#         # return cursor.fetchall()
#
#     def close(self):
#         """
#         Closes the current connection.
#
#         If a connection is currently open, this method will close it.
#         After calling this method, the connection will no longer be available.
#         """
#         if self.connection:
#             self.connection.close()
#
#
# if __name__ == '__main__':
#     db = Database()
#     for index, row in db.fetch_all('vias_ec', 'Provincia = "AZUAY"').iterrows():
#         print(row.keys())
#         break

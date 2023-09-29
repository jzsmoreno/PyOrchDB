import re
from typing import List

import numpy as np
import pandas as pd
import pyodbc
from pandas.core.frame import DataFrame
from pydbsmgr.utils.azure_sdk import StorageController

sql_types = ["FLOAT", "INT", "BIGINT", "DATE", "VARCHAR(MAX)"]
pandas_types = ["float64", "int32", "int64", "datetime64[ns]", "object"]
datatype_dict = dict(zip(pandas_types, sql_types))


class UploadToSQL:
    """Allows uploading a set of `.parquet` files to SQL tables"""

    def __init__(self, conn_string, container_name):
        self.controller = StorageController(conn_string, container_name)

    def upload_parquet(
        self, files: List[str], db_conn_string: str, directory: str, chunk_size: int = 20
    ):
        """Receives a list of the paths to the `.parquet` files to be uploaded to SQL"""
        username = input("Enter the database user : ")
        password = input("Enter the database password : ")
        db_conn_string = db_conn_string.replace("<username>", username)
        db_conn_string = db_conn_string.replace("<password>", password)
        print(db_conn_string)
        for file in files:
            df, file_name = self.controller.get_parquet(directory, file)
            df_chunks = np.array_split(df[0], chunk_size)

            for chunk in df_chunks:
                con = pyodbc.connect(db_conn_string, autocommit=True)
                cur = con.cursor()

                tables = pd.read_sql(
                    "SELECT table_name = t.name FROM sys.tables t INNER JOIN sys.schemas s ON t.schema_id = s.schema_id ORDER BY t.name;",
                    con,
                )
                print(tables)

                exist_table = tables["table_name"].isin([file_name[0]]).any()

                if not exist_table:
                    try:
                        print("Creating the tables...")
                        cur.execute(self._create_table_query(file_name[0], chunk))
                    except pyodbc.Error as e:
                        warning_type = "UserWarning"
                        msg = "It was not possible to create the table {%s}\n" % file_name[0]
                        msg += "Error: {%s}" % e
                        return print(f"{warning_type}: {msg}")

                """Insert data"""
                cur.fast_executemany = True
                cur.executemany(
                    self._insert_table_query(file_name[0], chunk),
                    [
                        [
                            None
                            if str(value) == "<NA>"
                            or str(value) == ""
                            or (isinstance(value, float) and np.isnan(value))
                            else value
                            for value in row
                        ]
                        for row in chunk.values.tolist()
                    ],
                )
                con.close()

                msg = "Table {%s}, successfully imported!" % file_name[0]
                print(f"{msg}")

                print(chunk)
                print(file_name[0])

    def _create_table_query(self, table_name: str, df: DataFrame) -> str:
        """Constructs the query that will be used to create the table"""
        query = "CREATE TABLE " + table_name + "("
        for j, column in enumerate(df.columns):
            matches = re.findall(r"([^']*)", str(df.iloc[:, j].dtype))
            dtype = datatype_dict[matches[0]]
            query += column + " " + dtype + ", "

        query = query[:-2]
        query += ")"
        return query

    def _insert_table_query(self, table_name: str, df: DataFrame) -> str:
        """Constructs the query to insert all rows that are in the `DataFrame`."""
        query = "INSERT INTO %s({0}) values ({1})" % (table_name)
        query = query.format(",".join(df.columns), ",".join("?" * len(df.columns)))
        return query

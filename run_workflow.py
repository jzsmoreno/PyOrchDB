import sys
import re

from merge_by_lev import tabulate
from PyOrchDB.main import ETLWorkflow

if __name__ == "__main__":
    print("Start run_workflow.py")
    storage_name = sys.argv[1]
    conn_string = sys.argv[2]
    container_name = sys.argv[3]
    resource_group_name = sys.argv[4]
    exclude_files = sys.argv[5]
    directory = sys.argv[6]
    db_conn_string = sys.argv[7:]

    project_name = "Rotacion"  # input("Insert project name (first directory in the container) : ")

    db_conn_string = " ".join(db_conn_string)
    db_conn_string = db_conn_string.strip()

    if "<username>" in db_conn_string:
        db_conn_username = "sqladminsandbox"  # input("Insert your database username : ")
        db_conn_string = db_conn_string.replace("<username>", db_conn_username)

    if "<password>" in db_conn_string:
        db_conn_pwd = "tzmRV+Pm4rSA"  # input("Insert your database password : ")
        db_conn_string = db_conn_string.replace("<password>", db_conn_pwd)

    initial_pattern_db = re.compile(r"\{(ODBC Driver \d{2} for SQL Server|SQL Server)\}")

    db_conn_string = initial_pattern_db.sub("{ODBC Driver 17 for SQL Server}", db_conn_string)

    handler = ETLWorkflow(
        resource_group_name,
        conn_string,
        container_name,
        project_name,
        exclude_files,
        directory,
        db_conn_string,
    )

    # Run the workflow with all its steps
    handler.build(dist_min=12, delete_catalog=True)
    print("============================================")
    print("The names of the tables to be processed are as follows :")
    print(tabulate(handler.table_data, headers=["index", "names"], tablefmt="grid"))
    print("============================================")
    rename_tables = "y"  # input("Do you want to rename the tables? [y/n] : ")
    rename_manually = False
    if rename_tables == "y":
        rename_manually = "n"  # input("Do you want to rename the tables manually? [y/n] : ")
        rename_manually = rename_manually == "y"
    handler.curate(
        fast_execution=False,
        rename_tables=rename_tables,
        rename_manually=rename_manually,
    )
    handler.load()
    handler.upload(char_length=5000)

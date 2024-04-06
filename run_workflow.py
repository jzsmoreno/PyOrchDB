import sys

from PyOrchDB.main import ETLWorkflow

if __name__ == "__main__":
    print("Start run_workflow.py")
    conn_string = sys.argv[1]
    container_name = sys.argv[2]
    exclude_files = sys.argv[3]
    directory = sys.argv[4]
    db_conn_string = sys.argv[5:]

    project_name = input("Insert project name (first directory in the container) : ")
    db_conn_pwd = input("Insert your database password : ")

    handler = ETLWorkflow(
        conn_string,
        container_name,
        project_name,
        exclude_files,
        directory,
        db_conn_string,
        db_conn_pwd,
    )
    # Run the workflow with all its steps
    handler.build(dist_min=12, delete_catalog=True)
    handler.curate(fast_execution=False)
    handler.load()
    handler.upload()

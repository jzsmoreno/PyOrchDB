import sys

from pydbsmgr.utils.azure_sdk import StorageController

print("Start run_workflow.py")

if __name__ == "__main__":
    storage_name = sys.argv[1]
    conn_string = sys.argv[2]
    container_name = sys.argv[3]
    resource_group_name = sys.argv[4]

    controller = StorageController(conn_string, container_name)
    files = controller.get_all_blob()
    for file in files:
        print("File name : ", file)

    with open("output.txt", "w") as outfile:
        for row in files:
            outfile.write(row + "\n")

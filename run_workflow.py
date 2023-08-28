import sys
from typing import List

from pydbsmgr.utils.azure_sdk import StorageController

print("Start run_workflow.py")


def get_directories(files: List[str], subfolder_level: int = 0) -> List[str]:
    directories = set()
    for file in files:
        directories.add(file.split("/")[subfolder_level])
    if len(directories) > 1:
        print("The directories could be successfully inferred.")
        return list(directories)
    else:
        print("No directory found to process!")
        subfolder_level = input(
            "Inserts the level at which they can be found (number of subfolders) : "
        )
        get_directories(files, int(subfolder_level))


if __name__ == "__main__":
    storage_name = sys.argv[1]
    conn_string = sys.argv[2]
    container_name = sys.argv[3]
    resource_group_name = sys.argv[4]
    exclude_files = sys.argv[5]

    controller = StorageController(conn_string, container_name)
    files = controller.get_all_blob()

    for i, file in enumerate(files):
        if file.find(exclude_files) != -1:
            files.remove(file)
        else:
            print("File name : ", file)

    controller.set_BlobPrefix(files)
    directories = get_directories(files)
    print("The directories are as follows : ")
    print(directories)

    # with open("output.txt", "w") as outfile:
    #    for row in files:
    #        outfile.write(row + "\n")

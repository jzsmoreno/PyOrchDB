import os
import re
import sys
from io import TextIOWrapper
from typing import List

from merge_by_lev import *
from pydbsmgr import *
from pydbsmgr.utils.azure_sdk import StorageController
from pydbsmgr.utils.tools import ColumnsDtypes, erase_files, merge_by_coincidence


# Disable
def blockPrint():
    sys.stdout = open(os.devnull, "w")


# Restore
def enablePrint():
    sys.stdout = sys.__stdout__


print("Start run_workflow.py")


def get_directories(files: List[str], subfolder_level: int = 0) -> List[str]:
    """Get directories from list of files."""
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


def list_filter(elements: list, character: str) -> List[str]:
    """Function that filters a list from a criteria

    Args:
        elements (list): list of values to be filtered
        character (str): filter criteria

    Returns:
        List[str]: list of filtered elements
    """
    filter_elements = []
    for element in elements:
        if element.find(character) != -1:
            filter_elements.append(element)
    return filter_elements


def list_remove(elements: list, character: str) -> List[str]:
    """Function that removes items from a list based on a criteria

    Args:
        elements (list): list of values to be filtered
        character (str): filter criteria

    Returns:
        List[str]: list of filtered elements
    """
    for element in elements:
        if element.find(character) != -1:
            elements.remove(element)
    return elements


if __name__ == "__main__":
    storage_name = sys.argv[1]
    conn_string = sys.argv[2]
    container_name = sys.argv[3]
    resource_group_name = sys.argv[4]
    exclude_files = sys.argv[5]
    directory = sys.argv[6]

    controller = StorageController(conn_string, container_name)
    files = controller.get_all_blob()
    files = list_remove(files, exclude_files)

    controller.set_BlobPrefix(files)
    directories = get_directories(files)
    print("The directories are as follows : ")
    print(directories)

    erase_files()
    tables = []
    table_names = []
    client_name = input("Insert client name : ")
    for dir in directories:
        print(f"Computing: {dir}")
        blockPrint()
        filter_files = list_filter(files, dir)
        controller.set_BlobPrefix(filter_files)
        df_list, name_list = controller.get_excel_csv(directory, "\w+.(xlsx|csv)", True)
        enablePrint()
        for j, df in enumerate(df_list):
            blockPrint()
            df_list[j] = drop_empty_columns(df_list[j])
            df_list[j].columns = clean_transform(df_list[j].columns, False)
            df_list[j] = df_list[j].loc[:, ~df_list[j].columns.str.contains("^unnamed")]
            enablePrint()
            print(j, "| Progress :", "{:.2%}".format(j / len(df_list)))
            clearConsole()
        dfs, names, _ = merge_by_similarity(df_list, name_list, 9)

        for name in names:
            try:
                name = re.findall(name, "[A-Za-z]")[0]
            except:
                None
            table_names.append("TB_BI_" + client_name.lower() + (name.strip()).capitalize())
        tables += dfs

    blockPrint()
    for i, table in enumerate(tables):
        _, tables[i] = check_values(table, df_name=table_names[i], mode=False)
        handler = ColumnsDtypes(tables[i])
        tables[i] = handler.correct()
    enablePrint()
    # with open("output.txt", "w") as outfile:
    #    for row in files:
    #        outfile.write(row + "\n")

import os
import re
import sys
from typing import List

from merge_by_lev import *
from merge_by_lev.tools import check_empty_df
from pydbsmgr import *
from pydbsmgr.lightest import LightCleaner
from pydbsmgr.utils.azure_sdk import StorageController
from pydbsmgr.utils.tools import ColumnsDtypes, columns_check, erase_files, merge_by_coincidence

from utilities.catalog import EventController
from utilities.upload_to_sql import UploadToSQL


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
        return get_directories(files, int(subfolder_level))


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


def insert_period(
    df: DataFrame, df_name: str, REGEX_PATTERN: str = r"\d{4}-\d{2}-\d{2}"
) -> DataFrame:
    """Function that inserts the period column from the database name

    Args:
        df (`DataFrame`): database to which the column will be added
        df_name (`str`): name of the database

    Returns:
        DataFrame: resulting base with the period column
    """
    period_extract = re.findall(REGEX_PATTERN, df_name)
    if len(period_extract) > 0:
        period = period_extract[0]
    else:
        REGEX_PATTERN = r".*([1-2][0-9]{3})"
        period_extract = re.findall(REGEX_PATTERN, df_name)
        if len(period_extract) > 0:
            period = period_extract[0]
        else:
            period = ""
    cols = df.columns
    filter_cols = list_filter(cols, "periodo")

    if not len(filter_cols) > 0:
        df["periodo"] = period

    return df


with open("./utilities/config_data.yml", "r") as file:
    yaml_data = yaml.safe_load(file)

# Extract the columns to delete from the YAML
columns_to_delete = yaml_data["columns_to_delete"]

# Extract the columns to rename from the YAML
columns_to_rename = yaml_data["columns_to_rename"]


def remove_by_dict(df: DataFrame, to_delete: list) -> DataFrame:
    """Remove a set of columns from `DataFrame`

    Args:
        df (`DataFrame`): `DataFrame` from which columns will be removed
        to_delete (`list`): `list` of columns to be removed

    Returns:
        `DataFrame`: `DataFrame` without the columns to be removed
    """
    cols = set(df.columns)
    columns_to_keep = list(cols.difference(set(to_delete)))
    df = df[columns_to_keep].copy()
    return df


if __name__ == "__main__":
    storage_name = sys.argv[1]
    conn_string = sys.argv[2]
    container_name = sys.argv[3]
    resource_group_name = sys.argv[4]
    exclude_files = sys.argv[5]
    directory = sys.argv[6]
    db_conn_string = "Driver={SQL " + sys.argv[12]
    db_conn_string = db_conn_string.replace("{SQL Server}", "{ODBC Driver 17 for SQL Server}")

    project = input("Insert project name (first directory in the container) : ")
    controller = StorageController(conn_string, container_name)
    files = controller.get_all_blob()
    files = list_remove(files, exclude_files)
    # consult catalog
    manager = EventController(conn_string, container_name, project)
    try:
        manager.create_log(files)
    except:
        files = manager.diff(files)

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
        df_list, name_list = check_empty_df(df_list, name_list)
        enablePrint()
        for j, df in enumerate(df_list):
            blockPrint()
            df_list[j] = df_list[j].loc[:, ~df_list[j].columns.str.contains("^Unnamed")]
            df_list[j] = drop_empty_columns(df_list[j])
            df_list[j] = df_list[j].loc[:, ~df_list[j].columns.str.contains("^unnamed")]
            df_list[j] = columns_check(df_list[j])
            df_list[j].columns = clean_transform(df_list[j].columns, False)
            df_list[j] = insert_period(df_list[j], name_list[j])
            df_list[j] = remove_by_dict(df_list[j], columns_to_delete)
            df_list[j] = df_list[j].rename(columns=columns_to_rename)
            enablePrint()
            print(j, "| Progress :", "{:.2%}".format(j / len(df_list)))
            clearConsole()
        dfs, names, _ = merge_by_similarity(df_list, name_list, 9, 5)

        for name in names:
            try:
                name = re.findall(name, "[A-Za-z]")[0]
            except:
                None
            table_names.append("TB_BI_" + client_name.lower() + (dir.strip()).capitalize())
        tables += dfs

    print("Starting the cleaning process...")
    blockPrint()
    for i, table in enumerate(tables):
        if not isinstance(tables[i], DataFrame):
            tables[i] = tables[i].to_frame().reset_index()
        cleaner = LightCleaner(tables[i])
        tables[i] = cleaner.clean_frame()
        try:
            handler = ColumnsDtypes(tables[i])
            tables[i] = handler.correct()
        except:
            None
    enablePrint()

    print("Completed!")
    container_name = "processed"  # Is a fixed variable
    controller_ = StorageController(conn_string, container_name)
    controller_.write_parquet(project, tables, table_names)

    del tables, dfs, df_list, controller  # The ram is released

    files_processed = controller_.get_all_blob()

    # list of files to be read `.parquet`
    files_parquet = list_filter(files_processed, ".parquet")

    db_handler = UploadToSQL(conn_string, container_name)
    db_handler.upload_parquet(files_parquet, db_conn_string, project)

    del files_processed

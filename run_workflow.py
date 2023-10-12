import os
import re
import sys
from typing import List

from merge_by_lev import *
from merge_by_lev.schema_config import DataSchema
from merge_by_lev.tools import check_empty_df
from pydbsmgr import *
from pydbsmgr.lightest import LightCleaner
from pydbsmgr.utils.azure_sdk import StorageController
from pydbsmgr.utils.tools import ColumnsCheck, ColumnsDtypes, erase_files, merge_by_coincidence

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
    db_conn_string = db_conn_string.replace("{SQL Server}", "{ODBC Driver 18 for SQL Server}")

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
        manager.update(files)

    controller.set_BlobPrefix(files)
    directories = get_directories(files)
    print("The directories are as follows : ")
    print(directories)

    erase_files()
    tables = []
    table_names = []
    table_data = []
    client_name = input("Insert client name : ")
    for dir in directories:
        print(f"Computing: {dir}")
        blockPrint()
        filter_files = list_filter(files, dir)
        controller.set_BlobPrefix(filter_files)
        df_list, name_list = controller.get_excel_csv(directory, "\w+.(xlsx|csv)", True)
        df_list, name_list = check_empty_df(df_list, name_list)

        with open("./logs/" + dir + ".txt", "w") as outfile:
            for row in name_list:
                outfile.write(row + "\n")
        enablePrint()
        for j, df in enumerate(df_list):
            blockPrint()
            df_list[j] = df_list[j].loc[:, ~df_list[j].columns.str.contains("^Unnamed")]
            df_list[j] = drop_empty_columns(df_list[j])
            column_handler = ColumnsCheck(df_list[j])
            df_list[j] = column_handler.get_frame()
            df_list[j].columns = clean_transform(df_list[j].columns, False, remove_numeric=False)
            df_list[j].columns = df_list[j].columns.str.replace("__", "_")
            df_list[j] = insert_period(df_list[j], name_list[j])
            df_list[j] = remove_by_dict(df_list[j], columns_to_delete)
            df_list[j] = df_list[j].rename(columns=columns_to_rename)
            column_handler = ColumnsCheck(df_list[j])
            df_list[j] = column_handler._check_reserved_words()
            enablePrint()
            print(j, "| Progress :", "{:.2%}".format(j / len(df_list)))
            clearConsole()
        dfs, names, _ = merge_by_similarity(df_list, name_list, 9)

        for name in names:
            try:
                name = (name.split("-"))[-1]
                name = name.replace(" ", "")
                if name.find("Sheet") != -1:
                    name = ""
            except:
                None
            table_names.append("TB_BI_" + client_name.lower() + (dir.strip()).capitalize() + name)
            table_data.append([len(table_names), table_names[-1]])
        tables += dfs

    print("The table names will be as follows :")
    print(tabulate(table_data, headers=["index", "names"], tablefmt="grid"))
    rename_tables = input("You want to rename the tables [y/n] : ")
    if rename_tables == "y":
        for i, table_name in enumerate(table_names):
            message = "insert the new name for the table {%s} : " % table_name
            rename_table = input(message)
            table_names[i] = rename_table
    print("Starting the cleaning process...")

    for i, table in enumerate(tables):
        if not isinstance(tables[i], DataFrame):
            tables[i] = tables[i].to_frame().reset_index()
        cleaner = LightCleaner(tables[i])
        tables[i] = cleaner.clean_frame()
        handler = ColumnsDtypes(tables[i])
        tables[i] = handler.correct()
        schema_handler = DataSchema(tables[i])
        tables[i] = schema_handler.get_table()

    print("Completed!")
    container_name = "processed"  # Is a fixed variable
    controller_processed = StorageController(conn_string, container_name)
    files_not_loaded = controller_processed.write_pyarrow(project, tables, table_names)
    try:
        files_not_loaded = [
            (files_not).replace("TB_BI_" + client_name.lower(), "")
            for files_not in files_not_loaded
        ]
        manager.remove(files_not_loaded)
    except:
        None

    del tables, dfs, df_list, controller  # The ram is released

    files_processed = controller_processed.get_all_blob()
    files_filtered = []
    for dir in directories:
        files_filtered += list_filter(files_processed, dir)
    print("These are the tables that will be uploaded to SQL or will be updated :", files_filtered)
    # list of files to be read `.parquet`
    files_parquet = list_filter(files_filtered, ".parquet")

    db_handler = UploadToSQL(conn_string, container_name)
    db_handler.upload_parquet(files_parquet, db_conn_string, project)

    del files_processed, files_filtered

import os
import sys
import warnings
from abc import abstractmethod

import yaml
from merge_by_lev import *
from merge_by_lev.schema_config import DataSchema, StandardColumns
from merge_by_lev.tools import check_empty_df
from pyarrow import Table
from pydbsmgr import clean_transform, drop_empty_columns
from pydbsmgr.lightest import LightCleaner
from pydbsmgr.utils.azure_sdk import StorageController
from pydbsmgr.utils.tools import ColumnsCheck, ColumnsDtypes

from PyOrchDB.utilities import (
    EventController,
    get_directories,
    insert_period,
    list_filter,
    list_remove,
    remove_by_dict,
    set_table_names,
)


class ETLWorkflow:
    def __init__(
        self,
        resource_group_name: str,
        conn_string: str,
        container_name: str,
        project_name: str = "",
        exclude_files: str = "catalog",
        directory: str = "/",
        db_conn_string: str = "",
        db_conn_pwd: str = "your_password_here",
        client_name: str = "",
        ODBC_DRIVER: str = "18",
    ):
        self.conn_string = conn_string
        self.container_name = container_name
        self.resource_group_name = resource_group_name
        self.storage_name = conn_string.split(";")[1].split("=")[1]
        self.exclude_files = exclude_files
        self.directory = directory
        # Define the regular expression pattern
        pattern_db = re.compile(r"\{(ODBC Driver \d{2} for SQL Server|SQL Server)\}")
        # Perform the substitution
        if isinstance(db_conn_string, list):
            db_conn_string = db_conn_string[0]
        db_conn_string = pattern_db.sub(
            "{ODBC Driver %s for SQL Server}" % ODBC_DRIVER, db_conn_string
        )
        pattern_pwd = re.compile(r"\{your_password_here\}")
        db_conn_string = pattern_pwd.sub(db_conn_pwd, db_conn_string)
        self.db_conn_string = db_conn_string
        self.project = project_name

        self.controller = StorageController(self.conn_string, self.container_name)

        self.manager = EventController(self.conn_string, self.container_name, self.project)
        self.tables: list = []
        self.table_data: list = []
        self.table_names: list = []
        self.client_name = client_name

    def build(
        self,
        dist_min: int = 9,
        match_cols: int = 4,
        drop_empty: bool = False,
        add_config: bool = False,
        delete_catalog: bool = False,
        update_catalog: bool = True,
        **kwargs,
    ) -> None:
        """Building a data pipeline by downloading files from Azure Blob storage and creating tables"""
        print("\nStart building process...\n")
        files = self._get_file_list(**kwargs)
        if update_catalog:
            files = self._update_catalog(files, delete_catalog)
        else:
            if delete_catalog:
                warnings.warn(
                    "delete_catalog=True ignored because update_catalog=False", UserWarning
                )
            files = self.manager.diff(files)
        # Get all directories
        self.set_directories(files)
        self.add_config = add_config
        if self.add_config:
            self._load_config()
        for dir in self.directories:
            print(f"Processing {dir}")
            filter_files = list_filter(files, dir)
            self.controller.set_BlobPrefix(filter_files)
            try:
                df_list, name_list = self.controller.get_excel_csv(
                    self.directory, "\w+.(xlsx|csv)", True
                )
            except UnicodeDecodeError:
                df_list, name_list = self.controller.get_excel_csv(
                    self.directory, "\w+.(xlsx|csv)", True, encoding="latin-1"
                )
            df_list, name_list = check_empty_df(df_list, name_list)
            # Create the necessary logs
            self._update_logs(dir, name_list)
            errors = []
            for j, _ in enumerate(df_list):
                # Preliminary corrections
                print(f"Applying DataFrame corrections to {name_list[j]}")
                df_list[j] = self.fix(df_list[j])
                if df_list[j] is None:
                    errors.append(j)
                    continue
                # If necessary, the period column is inserted.
                df_list[j] = insert_period(df_list[j], name_list[j])
                # Additional operations on columns
                df_list[j] = self._ops_cols(df_list[j])
                # Supplemental verification
                column_handler = ColumnsCheck(df_list[j])
                df_list[j] = column_handler._check_reserved_words()
                # Progress is shown
                print(j, "| Progress :", "{:.2%}".format(j / len(df_list)))
                clearConsole()
            df_list, name_list = self._remove_errors(errors, df_list, name_list)
            # A concatenation is performed according to the similarity of the databases
            dfs, names, _ = merge_by_similarity(
                df_list, name_list, dist_min=dist_min, match_cols=match_cols, drop_empty=drop_empty
            )
            # Update the list of table names
            self._name_settings(names, dir)
            self.tables += dfs
        del dfs, df_list, column_handler

    def curate(
        self, rename_manually: bool = True, cleaning: bool = True, engine: str = "pyarrow", **kwargs
    ) -> List[Table] | List[DataFrame]:
        self.engine = engine
        """Processes the created database to load it into the Azure SQL database."""
        print("The names of the tables to be processed are as follows :")
        print(tabulate(self.table_data, headers=["index", "names"], tablefmt="grid"))
        rename_tables = input("You want to rename the tables [y/n] :")
        write_to_cloud = kwargs["write_to_cloud"] if "write_to_cloud" in kwargs else False
        if rename_tables == "y":
            if not rename_manually:
                self.table_names = set_table_names(self.table_names)
            else:
                for i, table_name in enumerate(self.table_names):
                    message = "insert the new name for the table {%s} : " % table_name
                    rename_table = input(message)
                    self.table_names[i] = rename_table
        for i, _ in enumerate(self.tables):
            if not isinstance(self.tables[i], DataFrame):
                self.tables[i] = self.tables[i].to_frame().reset_index()
            if (
                self.table_names[i].find("Encuesta") != -1
                or self.table_names[i].find("Survey") != -1
            ):
                column_handler = StandardColumns(self.tables[i])
                self.tables[i] = column_handler.get_frame(
                    self.table_names[i] + ".json",
                    write_to_cloud,
                    self.conn_string,
                    self.container_name,
                )
                del column_handler
            if cleaning:
                print(f"Starting the cleaning process of {self.table_names[i]}")
                self.tables[i] = self.clean_db(self.tables[i], **kwargs)
                print("process completed!")
                clearConsole()
            handler = ColumnsDtypes(self.tables[i])
            self.tables[i] = handler.correct()
            if engine == "pyarrow":
                schema_handler = DataSchema(self.tables[i])
                self.tables[i] = schema_handler.get_table()
        del handler
        return self.tables

    def load(self, container_name: str = "processed", engine: str = "pyarrow", **kwargs) -> None:
        print("Uploading data curated to Azure Blob storage...\n")
        format_type = kwargs["format_type"] if "format_type" in kwargs else "csv"
        encoding = kwargs["encoding"] if "encoding" in kwargs else "utf-8"
        self.loader = StorageController(self.conn_string, container_name)
        if engine == "pyarrow":
            files_not_loaded = self.loader.write_pyarrow(
                self.project, self.tables, self.table_names
            )
            self._remove_from_catalog(files_not_loaded)
        else:
            self.loader.upload_excel_csv(
                self.project, self.tables, self.table_names, format_type, encoding
            )
        del self.tables, self.controller, self.loader

    def upload(
        self,
        ram_usage: bool = False,
        container_name: str = "processed",
        tables: List[DataFrame] = [],
        names: List[str] = [],
        engine: str = "pyarrow",
        with_cache: bool = True,
        **kwargs,
    ) -> None:
        print("Uploading data to Azure SQL Database...\n")
        if with_cache:
            from PyOrchDB.utilities.table_upload import UploadToSQL
        else:
            from PyOrchDB.utilities.upload_to_sql import UploadToSQL
        pwd_verbose = kwargs["pwd_verbose"] if "pwd_verbose" in kwargs else False
        if ram_usage == False and engine == "pyarrow":
            self.loader = StorageController(self.conn_string, container_name)
            files_processed = self.loader.get_all_blob(self.project)
            files_filtered: list = []
            try:
                _ = self.directories[0]
            except AttributeError:
                self.set_directories(files_processed)
            for dir in self.directories:
                files_filtered += list_filter(files_processed, dir, True)
            print(
                "These are the tables that will be uploaded to SQL or will be updated :",
                files_filtered,
            )
            files_parquet = list_filter(files_filtered, ".parquet")
            db_handler = UploadToSQL(self.conn_string, container_name)
            db_handler.upload_parquet(files_parquet, self.db_conn_string, self.project, **kwargs)
        else:
            pass
        print("process completed!")

    @abstractmethod
    def clean_db(self, table: DataFrame, **kwargs) -> DataFrame:
        """Performs cleaning tasks"""
        fast_execution = kwargs["fast_execution"] if "fast_execution" in kwargs else True
        cleaner = LightCleaner(table)
        table = cleaner.clean_frame(fast_execution=fast_execution)
        del cleaner
        return table

    def fix(self, df: DataFrame, drop_columns: bool = False) -> DataFrame:
        """Fix the dataframe according to predefined rules"""
        try:
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        except TypeError as e:
            # This happens when there is only one column left after dropping Unnamed columns
            warning_type = "UserWarning"
            msg = "There is a problem with the database so it will not be processed, perform correction manually."
            msg += "Error: {%s}" % e
            print(f"{warning_type}: {msg}")
            return None
        if drop_columns:
            df = drop_empty_columns(df)
        column_handler = ColumnsCheck(df)
        df = column_handler.get_frame()
        df.columns = clean_transform(df.columns, False, remove_numeric=False)
        df.columns = df.columns.str.replace("__", "_")
        return df

    def set_directories(self, files: List[str]) -> List[str]:
        """Inspects all directories and returns a list of names"""
        self.directories = sorted(self._read_root(files))
        print("The directories are as follows : ")
        print(self.directories)
        return self.directories

    def _remove_errors(
        self, index_errors: List[int], df_list: List[DataFrame], name_list: List[str]
    ) -> List[DataFrame]:
        """Removes errors from dataframes in case they were not caught during processing"""
        # check that index_errors is not empty
        if len(index_errors) > 0:
            for index_error in index_errors:
                df_list.pop(index_error)
                name_list.pop(index_error)
        return df_list, name_list

    def _name_settings(self, names: List[str], dir: str) -> None:
        """Create a unique name for each database based on its content."""
        for name in names:
            try:
                name = (name.split("-"))[-1]
                name = name.replace(" ", "")
                if name.find("Sheet") != -1 or name.find("Hoja") != -1:
                    name = ""
            except:
                None
            self.table_names.append(
                "TB_BI_" + self.client_name.lower() + (dir.strip()).capitalize() + name
            )
            self.table_data.append([len(self.table_names), self.table_names[-1]])

    def _load_config(self, yaml_path: str = "./utilities/config_data.yml") -> None:
        try:
            with open(yaml_data, "r") as file:
                yaml_data = yaml.safe_load(file)
            self.yaml_data = yaml_data
        except:
            raise Exception("Error loading config file.")

    def _ops_cols(self, df: DataFrame) -> DataFrame:
        if self.add_config:
            df = remove_by_dict(df, self.yaml_data["columns_to_delete"])
            df = df.rename(columns=self.yaml_data["columns_to_rename"])
        return df

    def _update_logs(self, dir: str, name_list: List[str], logs_path: str = "./logs/") -> None:
        assert logs_path.endswith("/"), "Directory not valid, must end with backslash."
        try:
            os.path.exists(logs_path)
        except:
            print(f"{logs_path} does not exist, it will be created.")
            os.makedirs(logs_path)

        with open(logs_path + dir + ".txt", "w") as outfile:
            for row in name_list:
                outfile.write(row + "\n")

    def _read_root(self, files) -> List[str]:
        """Read a list of file names in blob storage and return their root directories"""
        self.controller.set_BlobPrefix(files)
        return get_directories(files)

    def _update_catalog(self, files, delete_catalog) -> None:
        if delete_catalog:
            self.manager._clean()
        if self._consult_catalog(files) is None:
            self.manager.create_log(files, delete_catalog)
        else:
            files = self.manager.diff(files)
            self.manager.update(files)
        return files

    def _remove_from_catalog(self, files_not_loaded) -> None:
        # Remove from catalog any files that could not be processed
        try:
            files_not_loaded = [
                (files_not).replace("TB_BI_" + self.client_name.lower(), "")
                for files_not in files_not_loaded
            ]
            self.manager.remove(files_not_loaded)
        except:
            pass

    def _get_file_list(self, **kwargs) -> List[str]:
        filter_criteria = kwargs["filter_criteria"] if "filter_criteria" in kwargs else self.project
        exclude_files = kwargs["exclude_files"] if "exclude_files" in kwargs else self.exclude_files
        files = self.controller.get_all_blob(filter_criteria)
        files = list_remove(files, exclude_files)
        return files

    def _consult_catalog(self, files) -> List[str] | None:
        is_catalog = self.manager.audit()

        if is_catalog is None:
            return is_catalog
        return files

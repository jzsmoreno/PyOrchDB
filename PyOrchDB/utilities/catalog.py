import datetime
import sys
from typing import List

import pandas as pd
import yaml
from pandas.core.frame import DataFrame
from pandas.errors import EmptyDataError
from pydbsmgr.utils.azure_sdk import StorageController


def set_table_names(
    table_names: List[str],
    default_name: bool = False,
    file_path: str = "./utilities/table_names.yml",
) -> List[str]:
    """function that takes the default names for the tables in the file `table_names.yml`

    Parameters
    ----------
    table_names : List[`str`]
        list of original names of the tables.
    default_name : `bool`
        if `True`, the default name will be used when there is no match.
    file_path : `str`
        path where the catalog of tables is located.

    Returns
    -------
    List[`str`]
        names changed to those written in the `.yml` file.
    """
    with open(file_path, "r") as file:
        yaml_table = yaml.safe_load(file)

    keys_tables = [k.split()[0] for k in yaml_table.keys()]
    for i, name in enumerate(table_names):
        for key_name in keys_tables:
            if name.find(key_name) != -1:
                if type(yaml_table[key_name]) == str:
                    table_names[i] = yaml_table[key_name]
                else:
                    sub_keys_tables = [k.split()[0] for k in yaml_table[key_name].keys()]
                    sub_keys_tables.remove("None")
                    for sub_key_name in sub_keys_tables:
                        if name.find(sub_key_name) != -1:
                            table_names[i] = yaml_table[key_name][sub_key_name]
                        elif default_name:
                            table_names[i] = yaml_table[key_name]["None"]
    return table_names


class EventController(StorageController):
    def __init__(self, connection_string: str, container_name: str, directory: str):
        super().__init__(connection_string, container_name)
        self.cat_ = pd.DataFrame()
        self.directory = directory

    def create_log(
        self, files: List[str], overwrite: bool = False, delete_catalog: bool = False
    ) -> None:
        events = pd.DataFrame()
        events["files"] = files
        events["datetime"] = datetime.datetime.now()
        if delete_catalog:
            overwrite = True
        super().upload_excel_csv(self.directory, [events], ["catalog"], overwrite=overwrite)

    def audit(self) -> DataFrame | None:
        try:
            self.cat_, _ = super().get_excel_csv(self.directory, "catalog.csv")
        except EmptyDataError:
            return None
        if len(self.cat_) > 0:
            return self.cat_[0]
        return None

    def remove(self, files_not_loaded: List[str]) -> None:
        self.cat_, _ = super().get_excel_csv(self.directory, "catalog.csv")
        self.cat_ = self.cat_[0]
        self.cat_ = self.cat_[~self.cat_["files"].str.contains("|".join(files_not_loaded))]
        super().upload_excel_csv(self.directory, [self.cat_], ["catalog"], overwrite=True)

    def update(self, files: List[str], overwrite: bool = True) -> None:
        events = pd.DataFrame()
        events["files"] = files
        events["datetime"] = datetime.datetime.now()
        catalog = self.audit()
        catalog = pd.concat([catalog, events], ignore_index=True)
        super().upload_excel_csv(self.directory, [catalog], ["catalog"], overwrite=overwrite)

    def _clean(self) -> None:
        super().upload_excel_csv(self.directory, [pd.DataFrame()], ["catalog"], overwrite=True)

    def diff(self, files: List[str]) -> List[str]:
        cat_ = self.audit()
        if cat_ is not None:
            cat_list = set((cat_)["files"])
            new_files = list(set(files).difference(cat_list))
            if len(new_files) > 0:
                return new_files
            else:
                sys.exit("There is nothing new to upload")
        else:
            return files

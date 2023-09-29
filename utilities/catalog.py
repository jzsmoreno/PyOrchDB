import datetime
import sys
from typing import List

import pandas as pd
from pandas.core.frame import DataFrame
from pydbsmgr.utils.azure_sdk import StorageController


class EventController(StorageController):
    def __init__(self, connection_string: str, container_name: str, directory: str):
        super().__init__(connection_string, container_name)
        self.cat_ = pd.DataFrame()
        self.directory = directory

    def create_log(self, files: List[str], overwrite: bool = False) -> None:
        events = pd.DataFrame()
        events["files"] = files
        events["datetime"] = datetime.datetime.now()
        super().upload_excel_csv(self.directory, [events], ["catalog"], overwrite=overwrite)

    def audit(self) -> DataFrame:
        self.cat_, _ = super().get_excel_csv(self.directory, "catalog.csv")
        if len(self.cat_) > 0:
            return self.cat_[0]
        else:
            return None

    def remove(self, files_not_loaded: List[str]) -> None:
        self.cat_, _ = super().get_excel_csv(self.directory, "catalog.csv")
        self.cat_ = self.cat_[0]
        self.cat_ = self.cat_[~self.cat_["files"].str.contains("|".join(files_not_loaded))]
        super().upload_excel_csv(self.directory, [self.cat_], ["catalog"], overwrite=True)

    def update(self, events: DataFrame, overwrite: bool = True) -> None:
        self.cat_ = pd.concat([self.cat_, events], ignore_index=True)
        super().upload_excel_csv(self.directory, [self.cat_], ["catalog"], overwrite=overwrite)

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

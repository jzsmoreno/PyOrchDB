import datetime
import sys
from typing import List, Optional

import pandas as pd
import yaml
from pandas.errors import EmptyDataError
from pydbsmgr.utils.azure_sdk import StorageController


def load_table_names(file_path: str) -> dict:
    """Load table names from a YAML file."""
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def set_table_names(
    table_names: List[str],
    default_name: bool = False,
    file_path: str = "./utilities/table_names.yml",
) -> List[str]:
    """Map original table names to those in the YAML file."""
    yaml_table = load_table_names(file_path)
    keys_tables = [k.split()[0] for k in yaml_table.keys()]

    updated_names = []
    for name in table_names:
        new_name = name
        for key_name in keys_tables:
            if key_name in name:
                value = yaml_table[key_name]
                if isinstance(value, str):
                    new_name = value
                    break
                else:
                    sub_keys_tables = [k.split()[0] for k in value.keys() if k != "None"]
                    for sub_key_name in sub_keys_tables:
                        if sub_key_name in name:
                            new_name = value[sub_key_name]
                            break
                    else:
                        if default_name:
                            new_name = value.get("None", name)
                break
        updated_names.append(new_name)

    return updated_names


class EventController(StorageController):
    def __init__(self, connection_string: str, container_name: str, directory: str):
        super().__init__(connection_string, container_name)
        self.catalog = pd.DataFrame()
        self.directory = directory

    def create_log(
        self, files: List[str], overwrite: bool = False, delete_catalog: bool = False
    ) -> None:
        """Create a log of uploaded files with timestamps."""
        events = pd.DataFrame({"files": files, "datetime": datetime.datetime.now()})
        if delete_catalog:
            overwrite = True
        self.upload_catalog(events, overwrite)

    def audit(self) -> Optional[pd.DataFrame]:
        """Retrieve the current catalog of files."""
        try:
            self.catalog, _ = super().get_excel_csv(self.directory, "catalog.csv")
        except EmptyDataError:
            return None

        if len(self.catalog) > 0:
            return self.catalog[0]
        return None

    def remove(self, files_not_loaded: List[str]) -> None:
        """Remove entries from the catalog for specified files."""
        self.catalog, _ = super().get_excel_csv(self.directory, "catalog.csv")
        if not self.catalog.empty:
            self.catalog = self.catalog[
                ~self.catalog["files"].str.contains("|".join(files_not_loaded))
            ]
            self.upload_catalog(self.catalog)

    def update(self, files: List[str], overwrite: bool = True) -> None:
        """Update the catalog with new entries."""
        events = pd.DataFrame({"files": files, "datetime": datetime.datetime.now()})
        if (catalog := self.audit()) is not None:
            events = pd.concat([catalog, events], ignore_index=True)
        self.upload_catalog(events, overwrite)

    def _clean(self) -> None:
        """Clear the catalog."""
        self.upload_catalog(pd.DataFrame(), True)

    def diff(self, files: List[str]) -> List[str]:
        """Find new files not in the catalog."""
        if (cat := self.audit()) is not None and not cat.empty:
            cat_list = set(cat["files"])
            new_files = list(set(files).difference(cat_list))
            if new_files:
                return new_files
            else:
                sys.exit("There is nothing new to upload")
        return files

    def upload_catalog(self, catalog: pd.DataFrame, overwrite: bool = False) -> None:
        """Upload the catalog to Azure storage."""
        super().upload_excel_csv(self.directory, [catalog], ["catalog"], overwrite=overwrite)

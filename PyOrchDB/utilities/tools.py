import logging
import re
from typing import List, Tuple

import pandas as pd
from pydbsmgr.fast_upload import UploadToSQL
from pydbsmgr.utils.azure_sdk import StorageController
from pydbsmgr.utils.tools import ColumnsDtypes

# Setting up basic configuration for logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlobPrefix:
    def __init__(self, name=""):
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if isinstance(name, str):
            self._name = name
        else:
            raise ValueError("Name must be provided as a string.")


class DatabaseManager(StorageController, UploadToSQL):
    """Manages the uploading of `.parquet` files to SQL tables."""

    def __init__(
        self, connection_string: str, container_name: str, database_connection_string: str
    ):
        """
        Initialize the DatabaseManager with Azure and SQL connections.

        Parameters
        ----------
        connection_string : `str`
            Connection string for Azure Storage. This is used to authenticate and connect
            to the Azure Blob Storage account.
        container_name : `str`
            Name of the Azure Blob container where the files are stored. This is used to
            access the container for reading or writing data.
        database_connection_string : `str`
            Connection string for the SQL database. This is used to establish a connection
            to the SQL database for data operations such as inserting or querying tables.

        Returns
        -------
        None
            This function initializes the connections but does not return any value.
        """
        super().__init__(connection_string, container_name)
        super(UploadToSQL, self).__init__(database_connection_string)
        self._verbose = True

    def upload(
        self,
        files: List[str],
        directory: str,
        auto_resolve: bool = True,
        frac: float = 0.01,
        chunk_size: int = 20,
        char_length: int = 256,
        override_length: bool = True,
        **kwargs,
    ) -> None:
        """
        Uploads a collection of `.parquet` files to corresponding SQL tables.

        Parameters
        ----------
        files : `list`
            List of file patterns (regex) to match and identify the `.parquet` files to upload.
        directory : `str`
            Path to the directory in Azure Blob Storage where the `.parquet` files are stored.
        auto_resolve : `bool`
            Flag indicating whether to automatically resolve and infer column types
            based on the data in the `.parquet` files (default is True).
        frac : `float`
            Fraction of the data to sample for inferring column types (range: 0.0 to 1.0).
            A smaller value may speed up the inference process at the cost of accuracy.
        chunk_size : `int`
            The number of rows to include in each chunk when uploading data to the SQL database.
            This allows for efficient memory management and faster upload times.
        char_length : `int`
            Default length for `VARCHAR` columns in the SQL tables. This value is used when
            the length of a `VARCHAR` column cannot be automatically inferred.
        override_length : `bool`
            Flag indicating whether to override the existing column lengths in
            the SQL tables if they already exist. If set to True, the new length from
            `char_length` will be applied to columns.

        Returns
        -------
        None
            This function does not return any value. It performs the upload operation to the SQL database.
        """
        method = kwargs["method"] if "method" in kwargs else "append"
        for file_pattern in files:
            try:
                df, file_name = self.get_parquet(directory_name=directory, regex=file_pattern)
                if auto_resolve:
                    handler = ColumnsDtypes(df[0])
                    df[0] = handler.correct(sample_frac=frac)
                self.execute(
                    df=df[0],
                    table_name=file_name[0],
                    chunk_size=chunk_size,
                    method=method,
                    char_length=char_length,
                    override_length=override_length,
                    auto_resolve=auto_resolve,
                )
                logger.info(f"Successfully uploaded {file_pattern} to SQL table {file_name}.")
            except Exception as e:
                try:
                    self.execute(
                        df=df[0],
                        table_name=file_name[0],
                        chunk_size=chunk_size,
                        method="override",
                        char_length=char_length,
                        override_length=override_length,
                        auto_resolve=auto_resolve,
                    )
                    logger.info(f"Successfully uploaded {file_pattern} to SQL table {file_name}.")
                except:
                    logger.error(f"Failed to upload {file_pattern}: {str(e)}")


def get_directories(files: List[str], subfolder_level: int = 1) -> List[str]:
    """Get directories from list of files."""
    directories = set(file.split("/")[subfolder_level] for file in files)

    if directories:
        print("The directories could be successfully inferred.")
        return list(directories)
    else:
        print("No directory found to process!")
        subfolder_level = int(
            input("Insert the level at which they can be found (number of subfolders): ")
        )
        return get_directories(files, subfolder_level)


def list_filter(elements: List[str], character: str, lowercase: bool = False) -> List[str]:
    """Filter a list based on a criteria.

    Args:
        elements (List[str]): List of values to be filtered.
        character (str): Filter criteria.
        lowercase (bool): Allow string comparison by converting to lowercase.

    Returns:
        List[str]: List of filtered elements.
    """
    if lowercase:
        lower_elements = [element.lower() for element in elements]
        character = character.lower()
        return [elements[i] for i, elem in enumerate(lower_elements) if character in elem]

    return [element for element in elements if character in element]


def list_remove(elements: List[str], character: str) -> List[str]:
    """Remove items from a list based on a criteria.

    Args:
        elements (List[str]): List of values to be filtered.
        character (str): Filter criteria.

    Returns:
        List[str]: List of filtered elements.
    """
    return [element for element in elements if character not in element]


def insert_period(
    df: pd.DataFrame, df_name: str, regex_pattern: str = r"\d{4}-\d{2}-\d{2}"
) -> pd.DataFrame:
    """Insert the period column from the database name.

    Args:
        df (pd.DataFrame): Database to which the column will be added.
        df_name (str): Name of the database.
        regex_pattern (str): Regex pattern for extracting the period.

    Returns:
        pd.DataFrame: Resulting base with the period column.
    """
    period_extract = re.findall(regex_pattern, df_name)

    if not period_extract:
        regex_pattern = r".*([1-2][0-9]{3})"
        period_extract = re.findall(regex_pattern, df_name)

    period = period_extract[0] if period_extract else ""

    if "periodo" not in df.columns:
        df["periodo"] = period

    return df


def remove_by_dict(df: pd.DataFrame, to_delete: List[str]) -> pd.DataFrame:
    """Remove a set of columns from DataFrame.

    Args:
        df (pd.DataFrame): DataFrame from which columns will be removed.
        to_delete (List[str]): List of columns to be removed.

    Returns:
        pd.DataFrame: DataFrame without the columns to be removed.
    """
    columns_to_keep = [col for col in df.columns if col not in to_delete]
    return df[columns_to_keep].copy()

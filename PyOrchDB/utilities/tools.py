import re
from typing import List

from pandas.core.frame import DataFrame


def get_directories(files: List[str], subfolder_level: int = 1) -> List[str]:
    """Get directories from list of files."""
    directories = set()
    for file in files:
        directories.add(file.split("/")[subfolder_level])
    if len(directories) >= 1:
        print("The directories could be successfully inferred.")
        return list(directories)
    else:
        print("No directory found to process!")
        subfolder_level = input(
            "Inserts the level at which they can be found (number of subfolders) : "
        )
        return get_directories(files, int(subfolder_level))


def list_filter(elements: list, character: str, lowercase: bool = False) -> List[str]:
    """Function that filters a list from a criteria

    Args:
        elements (`list`): list of values to be filtered
        character (`str`): filter criteria
        lowercase (`bool`): allow `str` comparison by converting to lowercase

    Returns:
        List[`str`]: list of filtered elements
    """
    element_copy = elements.copy()
    if lowercase:
        elements = map(lambda x: x.lower(), elements)
        character = character.lower()
    filter_elements = []
    for i, element in enumerate(elements):
        if element.find(character) != -1:
            filter_elements.append(element_copy[i])
    return filter_elements


def list_remove(elements: list, character: str) -> List[str]:
    """Function that removes items from a list based on a criteria

    Args:
        elements (`list`): list of values to be filtered
        character (`str`): filter criteria

    Returns:
        List[`str`]: list of filtered elements
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

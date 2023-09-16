from pydbsmgr import *
from pydbsmgr.utils.tools import replace_numbers_with_letters


def columns_check(cols: Index) -> List[str]:
    """Performs the relevant checks on the columns of the `DataFrame`"""

    def replace_commas(cols) -> List[str]:
        corrected_cols = []
        for col in cols:
            try:
                corrected_cols.append(col.replace(",", ""))
            except:
                corrected_cols.append(col)
        return corrected_cols

    def replace_numbers(cols) -> List[str]:
        corrected_cols = []
        for col in cols:
            corrected_cols.append(replace_numbers_with_letters(col))
        return corrected_cols

    def replace_duplicates(cols) -> List[str]:
        corrected_cols = []
        for col in cols:
            try:
                corrected_cols.append(col.replace("__", "_"))
            except:
                corrected_cols.append(col)
        return corrected_cols

    return replace_duplicates(replace_numbers(replace_commas(cols)))


if __name__ == "__main__":
    # Create a DataFrame
    data = {
        "Name 1": ["John", "Alice", "Bob"],
        "Age": [25, 30, 35],
        "Name 2": ["John", "Alice", "Bob"],
    }
    df = pd.DataFrame(data)

    df.columns = columns_check(df.columns)
    breakpoint()

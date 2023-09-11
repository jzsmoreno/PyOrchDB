import re

import numpy as np
import pandas as pd

REGEX_PATTER_YEAR = r"(\d{4}-\d{2}-\d{2}|.*([1-2][0-9]{3}))"


def insert_column_period(df_list, df_name_list):
    for df_idx in range(len(df_list)):
        periodo_extract = re.findall(REGEX_PATTER_YEAR, df_name_list[df_idx])
        if periodo_extract:
            periodo = periodo_extract[-1]
        else:
            periodo = np.nan

        df_list[df_idx]["periodo"] = periodo

    return df_list

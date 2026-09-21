from typing import Any, Dict, List

import pandas as pd


def concatenate_sheets(
    loaded_sheets: List[Dict[str, Any]],
) -> pd.DataFrame:
    dataframes = [
        sheet["dataframe"].copy()
        for sheet in loaded_sheets
        if sheet.get("dataframe") is not None
        and not sheet["dataframe"].empty
    ]

    if not dataframes:
        return pd.DataFrame()

    concatenated_dataframe = pd.concat(
        dataframes,
        ignore_index=True,
        sort=False,
        copy=False,
    )

    metadata_columns = [
        "fichier_source",
        "feuille_source",
        "ligne_source",
    ]

    other_columns = [
        column
        for column in concatenated_dataframe.columns
        if column not in metadata_columns
    ]

    return concatenated_dataframe[
        metadata_columns + other_columns
    ]
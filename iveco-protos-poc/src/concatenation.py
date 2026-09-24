import pandas as pd


def concatenate_sheets(loaded_sheets):
    frames = [x["dataframe"].copy() for x in loaded_sheets if x.get("dataframe") is not None and not x["dataframe"].empty]
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def split_business_tables(dataframe: pd.DataFrame) -> dict:
    empty = dataframe.iloc[0:0].copy() if not dataframe.empty else pd.DataFrame()
    if dataframe.empty or "phase" not in dataframe.columns:
        return {"etude": empty, "fabrication": empty, "planning": empty, "couts": empty, "autres": empty}
    return {
        "etude": dataframe[dataframe["phase"].eq("ETUDE")].copy(),
        "fabrication": dataframe[dataframe["phase"].eq("FABRICATION")].copy(),
        "planning": dataframe[dataframe["phase"].eq("PLANNING")].copy(),
        "couts": dataframe[dataframe["phase"].eq("COUT")].copy(),
        "autres": dataframe[dataframe["phase"].eq("AUTRE")].copy(),
    }

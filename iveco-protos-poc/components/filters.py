import pandas as pd
import streamlit as st


def apply_filters(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty: return dataframe.copy()
    result = dataframe.copy()
    with st.sidebar:
        st.divider(); st.markdown("## Filtres")
        for col, label in [("prototype", "Prototype"), ("phase", "Phase"), ("departement", "Département"), ("domaine_systeme", "Domaine"), ("systeme", "Système"), ("ft", "FT")]:
            if col not in result.columns: continue
            options = sorted(result[col].dropna().astype(str).unique().tolist())
            if not options: continue
            selected = st.multiselect(label, options, default=options, key=f"filter_{col}")
            result = result[result[col].astype(str).isin(selected)] if selected else result.iloc[0:0]
        search = st.text_input("Recherche", placeholder="P1, 061321, Dashboard...")
        if search and not result.empty:
            mask = result.astype("string").fillna("").apply(lambda s: s.str.contains(search, case=False, regex=False)).any(axis=1)
            result = result[mask]
        st.info(f"{len(result):,} ligne(s) sélectionnée(s)")
    return result

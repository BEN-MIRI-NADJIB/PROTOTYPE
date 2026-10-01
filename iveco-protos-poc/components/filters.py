import pandas as pd
import streamlit as st


def apply_filters(ft: pd.DataFrame) -> pd.DataFrame:
    """Filtres globaux : agissent sur tous les onglets (hors qualité des données)."""
    if ft.empty:
        return ft.copy()
    out = ft.copy()
    with st.sidebar:
        st.divider()
        st.markdown("## Filtres")
        protos = sorted(out["prototype"].dropna().unique())
        sel = st.multiselect("Prototype", protos, default=protos)
        out = out[out["prototype"].isin(sel)]
        for col, label in (("departement", "Département"), ("niveau_risque", "Niveau de risque"), ("situation", "Situation")):
            opts = sorted(out[col].dropna().unique())
            if opts:
                chosen = st.multiselect(label, opts, default=[], placeholder="Tous")
                if chosen:
                    out = out[out[col].isin(chosen)]
        if st.toggle("Seulement les FT à risque", value=False, help="Niveau modéré, élevé ou critique (score 21 et plus)."):
            out = out[out["score_risque"] >= 21]
        show_unfollowed = st.toggle("Inclure les FT sans aucun statut", value=False, help="FT sans statut étude ni fabrication (ex. P4 et P5) : elles ne portent aucune information de risque.")
        if not show_unfollowed:
            out = out[~out["couverture"].eq("Aucun statut")]
        q = st.text_input("Recherche FT / description", placeholder="61321, dashboard...")
        if q:
            mask = out["ft"].astype(str).str.contains(q.lstrip("0"), case=False, regex=False) | out["description"].astype(str).str.contains(q, case=False, regex=False)
            out = out[mask]
        st.info(f"{len(out):,} FT sélectionnée(s)")
    return out

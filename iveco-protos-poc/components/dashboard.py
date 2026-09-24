import pandas as pd
import streamlit as st


def _pct(a, b): return 0 if not b else 100*a/b


def display_dashboard(dataframe: pd.DataFrame, tables: dict, impacts: pd.DataFrame, validation: dict, costs_kpis: dict):
    st.subheader("Synthèse exécutive")
    study, fabrication = tables["etude"], tables["fabrication"]
    k = st.columns(6)
    k[0].metric("Prototypes", dataframe.get("prototype", pd.Series(dtype=str)).nunique())
    k[1].metric("Lignes étude", len(study))
    k[2].metric("Lignes fabrication", len(fabrication))
    k[3].metric("Risques critiques", int(impacts.get("niveau_risque", pd.Series(dtype=str)).eq("CRITIQUE").sum()) if not impacts.empty else 0)
    k[4].metric("Risques élevés", int(impacts.get("niveau_risque", pd.Series(dtype=str)).eq("ELEVE").sum()) if not impacts.empty else 0)
    k[5].metric("Qualité", f"{validation['quality_score']:.1f} %")
    st.markdown("### Étude vs fabrication")
    c1, c2, c3 = st.columns(3)
    c1.metric("Part étude", f"{_pct(len(study), max(len(study)+len(fabrication),1)):.1f} %")
    c2.metric("Part fabrication", f"{_pct(len(fabrication), max(len(study)+len(fabrication),1)):.1f} %")
    c3.metric("Coûts détectés", f"{costs_kpis['total_cost']:,.1f}")
    if not impacts.empty:
        st.markdown("### Priorités")
        cols = [c for c in ["prototype", "ft", "description", "phase_origine", "statut", "etape_impactee", "niveau_risque", "score_risque", "consequence"] if c in impacts.columns]
        st.dataframe(impacts[cols].head(20), use_container_width=True, hide_index=True)

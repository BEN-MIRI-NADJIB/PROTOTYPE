import streamlit as st

STATUS_COLORS = {"KO": "#b91c1c", "EN RETARD": "#ea580c", "MANQUANT": "#9333ea", "A RISQUE": "#d97706", "EN COURS": "#0891b2",
                 "OK": "#15803d", "TERMINE": "#4ade80", "NON RENSEIGNE": "#94a3b8", "ANNULE": "#64748b"}
LEVEL_COLORS = {"FAIBLE": "#15803d", "MODERE": "#d97706", "ELEVE": "#ea580c", "CRITIQUE": "#b91c1c"}
LEVEL_ORDER = ["CRITIQUE", "ELEVE", "MODERE", "FAIBLE"]
STATUS_ORDER = ["KO", "EN RETARD", "MANQUANT", "A RISQUE", "EN COURS", "OK", "TERMINE", "NON RENSEIGNE"]
COLS_LABELS = {
    "prototype": "Prototype", "ft": "FT", "description": "Description", "departement": "Département", "criticite": "Criticité", "responsable": "Responsable",
    "etude_statut": "Statut étude", "etude_dmu": "DMU", "etude_statut_ft": "Statut FT", "dap_prevus": "DAP prévus", "dap_envoyes": "DAP envoyés",
    "dap_avancement_pct": "Avancement DAP", "dap_semaines": "Semaines DAP", "cid_nb": "Nb CID", "cid_statut": "Statut CID", "fab_statut": "Statut fabrication",
    "fab_etape": "Étape de montage", "fab_besoin_pieces": "Besoin pièces", "fab_reception_prevue": "Réception prévue", "fab_ecart_jours": "Écart (j)",
    "fab_fournisseur": "Fournisseur", "fab_plan_b": "Plan B", "consequence_vehicule": "Conséquence véhicule", "gravite_consequence": "Gravité",
    "situation": "Situation", "impact_consequence": "Impact et conséquence", "score_risque": "Score", "niveau_risque": "Niveau", "action_recommandee": "Action",
}


def inject_css():
    st.markdown("""<style>
    .stApp{background:#f4f7fa}.block-container{padding-top:1.2rem;max-width:1500px}
    [data-testid=stMetric]{background:#fff;border:1px solid #d8e2ea;border-radius:10px;padding:12px 16px;box-shadow:0 1px 2px rgba(0,51,77,.05)}
    [data-testid=stMetricLabel]{color:#475569}
    .hero{background:linear-gradient(90deg,#00334d,#006f95);color:#fff;border-radius:12px;padding:18px 24px;margin-bottom:14px}
    .hero h1{color:#fff;margin:0;font-size:1.7rem}.hero p{color:#cfe6f0;margin:4px 0 0}
    .stTabs [data-baseweb=tab]{font-weight:600}
    </style>""", unsafe_allow_html=True)


def table(df, **kw):
    """Tableau lisible : en-têtes en français, score en barre de progression."""
    cfg = {c: st.column_config.TextColumn(l) for c, l in COLS_LABELS.items() if c in df.columns}
    if "score_risque" in df.columns:
        cfg["score_risque"] = st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")
    if "dap_avancement_pct" in df.columns:
        cfg["dap_avancement_pct"] = st.column_config.ProgressColumn("Avancement DAP", min_value=0, max_value=100, format="%d %%")
    for c in ("fab_besoin_pieces", "fab_reception_prevue"):
        if c in df.columns:
            cfg[c] = st.column_config.DateColumn(COLS_LABELS[c], format="DD/MM/YYYY")
    for c in ("dap_prevus", "dap_envoyes", "fab_ecart_jours", "cid_nb"):
        if c in df.columns:
            cfg[c] = st.column_config.NumberColumn(COLS_LABELS[c], format="%d")
    kw.setdefault("height", 480)
    st.dataframe(df, column_config=cfg, hide_index=True, width="stretch", **kw)

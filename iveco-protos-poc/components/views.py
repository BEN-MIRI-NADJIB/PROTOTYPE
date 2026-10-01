import pandas as pd
import streamlit as st
from components import charts
from components.theme import STATUS_COLORS, table
from src.ft_model import BAD, SIT_BOTH, SIT_STUDY

ETUDE_COLS = ["ft", "description", "departement", "criticite", "responsable", "etude_statut", "etude_dmu", "etude_statut_ft", "dap_envoyes", "dap_prevus", "dap_avancement_pct", "dap_semaines", "cid_nb", "cid_statut", "score_risque"]
FAB_COLS = ["ft", "description", "departement", "fab_statut", "fab_etape", "fab_besoin_pieces", "fab_reception_prevue", "fab_ecart_jours", "fab_fournisseur", "fab_plan_b", "consequence_vehicule", "score_risque"]
IMPACT_COLS = ["prototype", "ft", "description", "situation", "niveau_risque", "score_risque", "etude_statut", "fab_statut", "impact_consequence", "action_recommandee"]


def _cols(df, cols):
    return df[[c for c in cols if c in df.columns]]


def overview(ft, summary, warnings):
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} alerte(s) de fiabilité sur les fichiers importés (détail dans l'onglet Qualité des données)"):
            for w in warnings:
                st.markdown(f"- {w}")
    if ft.empty:
        st.info("Aucune FT avec ces filtres.")
        return
    k = st.columns(6)
    k[0].metric("Prototypes", ft["prototype"].nunique())
    k[1].metric("FT suivies", f"{len(ft):,}")
    k[2].metric("Critiques", int(ft["niveau_risque"].eq("CRITIQUE").sum()))
    k[3].metric("Étude en risque", int(ft["etude_statut"].isin(BAD).sum()), help="KO, DAP en retard ou DMU borderline.")
    k[4].metric("Fabrication en retard", int(ft["fab_statut"].isin(BAD).sum()))
    k[5].metric("Étude → fabrication exposée", int(ft["situation"].isin([SIT_STUDY, SIT_BOTH]).sum()), help="FT dont l'étude est en risque alors que la fabrication en dépend.")
    c1, c2 = st.columns(2)
    with c1: charts.level_by_proto(ft)
    with c2: charts.heatmap(ft)
    st.markdown("#### Synthèse par prototype")
    table(summary, height=230)
    st.markdown("#### Les 15 FT les plus à risque")
    table(_cols(ft, IMPACT_COLS).head(15), height=420)


def prototype_view(ft):
    if ft.empty:
        st.info("Aucune FT avec ces filtres.")
        return
    protos = sorted(ft["prototype"].unique())
    choice = st.segmented_control("Prototype", protos, default=protos[0]) or protos[0]
    g = ft[ft["prototype"].eq(choice)]
    left, right = st.columns(2)
    with left:
        st.markdown("### Partie Étude")
        st.caption("Conception : DMU, DAP, CID, statut FT.")
        a, b, c = st.columns(3)
        a.metric("FT", len(g)); b.metric("En risque", int(g["etude_statut"].isin(BAD).sum())); c.metric("Avancement DAP", f"{g['dap_envoyes'].sum() / g['dap_prevus'].sum():.0%}" if g["dap_prevus"].sum() else "n/a")
        charts.status_bar(g, "etude_statut", "Statut étude")
        table(_cols(g.sort_values("score_risque", ascending=False), ETUDE_COLS), height=380)
    with right:
        st.markdown("### Partie Fabrication")
        st.caption("Approvisionnement : réception vs besoin, étape de montage, fournisseur, Plan B.")
        a, b, c = st.columns(3)
        a.metric("FT", len(g)); b.metric("En retard / manquant", int(g["fab_statut"].isin(BAD).sum())); c.metric("Écart moyen", f"{g.loc[g['fab_statut'].isin(BAD), 'fab_ecart_jours'].mean():.0f} j" if g["fab_ecart_jours"].notna().any() else "n/a")
        charts.status_bar(g, "fab_statut", "Statut fabrication")
        table(_cols(g.sort_values("score_risque", ascending=False), FAB_COLS), height=380)
    st.markdown("### Impact et conséquences : de l'étude vers la fabrication")
    table(_cols(g, IMPACT_COLS).drop(columns="prototype", errors="ignore"), height=420)


def impact_view(ft):
    if ft.empty:
        st.info("Aucune FT avec ces filtres.")
        return
    st.caption("Lecture : chaque bande part du statut de l'étude, passe par la situation de la FT, et arrive à la conséquence sur le véhicule. L'épaisseur est le nombre de FT.")
    charts.sankey(ft)
    c1, c2 = st.columns(2)
    with c1: charts.delays_by_step(ft)
    with c2: charts.delays_by_supplier(ft)
    st.markdown("#### FT à traiter en priorité")
    table(_cols(ft[ft["score_risque"] >= 21], IMPACT_COLS), height=520)


def etude_view(ft):
    if ft.empty:
        return
    c1, c2 = st.columns(2)
    with c1: charts.status_bar(ft, "etude_statut", "Statut étude")
    with c2: charts.dap_by_dept(ft)
    table(_cols(ft, ["prototype"] + ETUDE_COLS), height=600)


def fabrication_view(ft):
    if ft.empty:
        return
    c1, c2 = st.columns(2)
    with c1: charts.status_bar(ft, "fab_statut", "Statut fabrication")
    with c2: charts.gap_histogram(ft)
    table(_cols(ft, ["prototype"] + FAB_COLS), height=600)


def planning_view(plan):
    if plan.empty:
        st.info("Importer MASTER_SUIVI_PROTO.xlsm pour voir le planning.")
        return
    dept = st.segmented_control("Département", sorted(plan["departement"].dropna().unique()), default=plan.groupby("departement")["unit"].sum().idxmax())
    charts.planning_chart(plan, dept or plan["departement"].iloc[0])


def quality_view(ft_all, warnings):
    st.caption("Fiabilité des fichiers importés : ce qui est renseigné, ce qui ne l'est pas.")
    for w in warnings:
        st.warning(w, icon="⚠️")
    if ft_all.empty:
        return
    d = ft_all.groupby(["prototype", "couverture"]).size().reset_index(name="FT")
    import plotly.express as px
    fig = px.bar(d, x="prototype", y="FT", color="couverture", text="FT", color_discrete_map={"Complet": "#15803d", "Étude seule": "#0891b2", "Fabrication seule": "#d97706", "Aucun statut": "#94a3b8"}, title="Couverture des statuts par prototype")
    fig.update_layout(template="plotly_white", legend_title_text="", xaxis_title=None)
    st.plotly_chart(fig, width="stretch")

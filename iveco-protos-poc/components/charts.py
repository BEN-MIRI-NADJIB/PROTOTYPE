import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.theme import LEVEL_COLORS, LEVEL_ORDER, STATUS_COLORS, STATUS_ORDER, table
from src.ft_model import BAD, SIT_BOTH, SIT_FAB, SIT_STUDY

LAYOUT = dict(template="plotly_white", margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")


def _show(fig, **kw):
    fig.update_layout(**LAYOUT, **kw)
    st.plotly_chart(fig, width="stretch")


def status_bar(ft: pd.DataFrame, col: str, title: str):
    d = ft[col].value_counts().rename_axis("statut").reset_index(name="FT")
    d["statut"] = pd.Categorical(d["statut"], STATUS_ORDER, ordered=True)
    _show(px.bar(d.sort_values("statut"), x="statut", y="FT", color="statut", text="FT", color_discrete_map=STATUS_COLORS, title=title), showlegend=False, xaxis_title=None)


def level_by_proto(ft: pd.DataFrame):
    d = ft.groupby(["prototype", "niveau_risque"]).size().reset_index(name="FT")
    _show(px.bar(d, x="prototype", y="FT", color="niveau_risque", text="FT", category_orders={"niveau_risque": LEVEL_ORDER[::-1]}, color_discrete_map=LEVEL_COLORS, title="Niveau de risque par prototype"), xaxis_title=None)


def heatmap(ft: pd.DataFrame):
    ct = pd.crosstab(ft["etude_statut"], ft["fab_statut"]).reindex(index=[s for s in STATUS_ORDER if s in set(ft["etude_statut"])], columns=[s for s in STATUS_ORDER if s in set(ft["fab_statut"])], fill_value=0)
    fig = px.imshow(ct, text_auto=True, aspect="auto", color_continuous_scale="Blues", labels=dict(x="Statut fabrication", y="Statut étude", color="FT"), title="Étude vs fabrication : où se concentrent les FT")
    _show(fig)


def sankey(ft: pd.DataFrame):
    """Flux Étude -> Situation -> Gravité de la conséquence véhicule."""
    d = ft.assign(e="Étude : " + ft["etude_statut"], s="Situation : " + ft["situation"].str.title(), g="Conséquence : " + ft["gravite_consequence"].str.title())
    links = pd.concat([d.groupby(["e", "s"]).size().reset_index(name="n").set_axis(["src", "dst", "n"], axis=1),
                       d.groupby(["s", "g"]).size().reset_index(name="n").set_axis(["src", "dst", "n"], axis=1)])
    nodes = list(pd.unique(links[["src", "dst"]].values.ravel()))
    idx = {n: i for i, n in enumerate(nodes)}
    color = lambda n: next((c for k, c in STATUS_COLORS.items() if n == f"Étude : {k}"), "#006f95" if n.startswith("Situation") else "#475569")
    fig = go.Figure(go.Sankey(node=dict(label=nodes, pad=14, thickness=16, color=[color(n) for n in nodes]),
                              link=dict(source=links["src"].map(idx), target=links["dst"].map(idx), value=links["n"], color="rgba(0,111,149,.22)")))
    _show(fig, title="De l'étude à la conséquence sur le véhicule", height=480)


def delays_by_step(ft: pd.DataFrame):
    d = ft[ft["fab_statut"].isin(BAD) & ft["fab_etape"].notna()].groupby(["fab_etape", "fab_statut"]).size().reset_index(name="FT")
    if d.empty:
        st.info("Aucun retard ou manquant renseigné.")
        return
    order = d.groupby("fab_etape")["FT"].sum().sort_values().index
    _show(px.bar(d, y="fab_etape", x="FT", color="fab_statut", orientation="h", color_discrete_map=STATUS_COLORS, category_orders={"fab_etape": list(order)}, title="Retards par étape de montage"), yaxis_title=None)


def delays_by_supplier(ft: pd.DataFrame):
    d = ft[ft["fab_statut"].isin(BAD) & ft["fab_fournisseur"].notna()].groupby("fab_fournisseur").size().nlargest(12).reset_index(name="FT en retard")
    if d.empty:
        st.info("Aucun fournisseur renseigné sur les FT en retard.")
        return
    _show(px.bar(d.sort_values("FT en retard"), x="FT en retard", y="fab_fournisseur", orientation="h", color_discrete_sequence=["#ea580c"], title="Fournisseurs concernés par un retard"), yaxis_title=None)


def gap_histogram(ft: pd.DataFrame):
    d = ft.dropna(subset=["fab_ecart_jours"])
    if d.empty:
        return
    _show(px.histogram(d, x="fab_ecart_jours", nbins=30, color_discrete_sequence=["#006f95"], title="Écart réception prévue - besoin (jours, positif = en retard)", labels={"fab_ecart_jours": "jours"}), yaxis_title="FT")


def dap_by_dept(ft: pd.DataFrame):
    d = ft.dropna(subset=["dap_prevus"]).groupby("departement", dropna=False)[["dap_prevus", "dap_envoyes"]].sum().reset_index().melt("departement", var_name="type", value_name="DAP")
    if d.empty:
        return
    d["type"] = d["type"].map({"dap_prevus": "Prévus", "dap_envoyes": "Envoyés"})
    _show(px.bar(d, x="departement", y="DAP", color="type", barmode="group", color_discrete_sequence=["#94a3b8", "#006f95"], title="Avancement des DAP par département"), xaxis_title=None)


def planning_chart(plan: pd.DataFrame, dept: str):
    d = plan[plan["departement"].eq(dept)]
    _show(px.line(d, x="periode", y="cumul", color="category", markers=True, color_discrete_map={"PLAN": "#94a3b8", "SENT": "#006f95"}, title=f"Planning MASTER cumulé, {dept} : plan vs envoyé"), xaxis_title=None)

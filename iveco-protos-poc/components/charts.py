import pandas as pd
import plotly.express as px
import streamlit as st

COLORS = ["#00334d", "#006f95", "#00a3bd", "#15803d", "#b45309", "#b91c1c", "#7c3aed"]


def display_detailed_charts(dataframe: pd.DataFrame, impacts: pd.DataFrame, costs: pd.DataFrame):
    st.subheader("Analyses")
    if "phase" in dataframe.columns:
        summary = dataframe.groupby([c for c in ["prototype", "phase"] if c in dataframe.columns], dropna=False).size().reset_index(name="lignes")
        if not summary.empty and "prototype" in summary.columns:
            st.plotly_chart(px.bar(summary, x="prototype", y="lignes", color="phase", barmode="group", color_discrete_sequence=COLORS, title="Étude vs fabrication par prototype"), use_container_width=True)
    if not impacts.empty:
        c1, c2 = st.columns(2)
        with c1:
            risk = impacts["niveau_risque"].value_counts().rename_axis("risque").reset_index(name="nombre")
            st.plotly_chart(px.pie(risk, names="risque", values="nombre", hole=.55, color_discrete_sequence=COLORS, title="Répartition des risques"), use_container_width=True)
        with c2:
            if "etape_impactee" in impacts.columns:
                steps = impacts.dropna(subset=["etape_impactee"]).groupby("etape_impactee").size().nlargest(15).reset_index(name="risques")
                st.plotly_chart(px.bar(steps, x="risques", y="etape_impactee", orientation="h", color="risques", color_continuous_scale="Blues", title="Risques par étape"), use_container_width=True)
    if not costs.empty:
        group_cols = [c for c in ["prototype", "phase"] if c in costs.columns]
        if group_cols:
            cost_sum = costs.groupby(group_cols, dropna=False)["cout_detecte"].sum().reset_index()
            st.plotly_chart(px.bar(cost_sum, x=group_cols[0], y="cout_detecte", color=group_cols[-1], color_discrete_sequence=COLORS, title="Coûts détectés"), use_container_width=True)

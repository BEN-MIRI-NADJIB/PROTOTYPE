import time

import streamlit as st

from components.charts import display_detailed_charts
from components.dashboard import display_dashboard
from components.filters import apply_filters
from src.cleaning import clean_dataframe
from src.concatenation import concatenate_sheets
from src.costs import calculate_cost_kpis, extract_costs
from src.excel_loader import load_excel_files
from src.validation import validate_dataframe


st.set_page_config(
    page_title="IVECO Protos Intelligence",
    page_icon="IP",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
:root {
    --iveco-navy: #00334d;
    --iveco-blue: #006f95;
    --iveco-cyan: #00a3bd;
    --ink: #1f2937;
    --muted: #64748b;
    --surface: #ffffff;
    --line: #d8e2ea;
}

.stApp {
    background: #f3f6f8;
    color: var(--ink);
}

[data-testid="stHeader"] {
    background: rgba(243, 246, 248, 0.92);
    backdrop-filter: blur(10px);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #002b49 0%, #003b5c 100%);
}

[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] button {
    color: #ffffff !important;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [role="combobox"],
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #111827 !important;
}

[data-testid="stSidebar"] button {
    background: rgba(255, 255, 255, 0.12) !important;
    border: 1px solid rgba(255, 255, 255, 0.28) !important;
}

[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

[data-testid="stMetricValue"] {
    color: var(--iveco-navy);
    font-weight: 750;
}

.workspace-header {
    border: 1px solid var(--line);
    border-left: 5px solid var(--iveco-blue);
    background: var(--surface);
    padding: 18px 22px;
    margin-bottom: 18px;
}

.workspace-title {
    margin: 0;
    color: var(--iveco-navy);
    font-size: 26px;
    font-weight: 760;
}

.workspace-subtitle {
    margin: 6px 0 0 0;
    color: var(--muted);
    font-size: 14px;
}

.status-card,
.success-card,
.notice-card {
    border-radius: 8px;
    padding: 14px 16px;
    margin: 12px 0;
    background: var(--surface);
    border: 1px solid var(--line);
}

.success-card {
    border-left: 5px solid #15803d;
}

.notice-card {
    border-left: 5px solid #b45309;
}

.section-title {
    color: var(--iveco-navy);
    font-size: 20px;
    font-weight: 720;
    margin: 12px 0;
}

.stButton > button,
.stDownloadButton > button {
    border: 0;
    border-radius: 6px;
    color: white !important;
    font-weight: 650;
    background: var(--iveco-blue);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #e8eef3;
    border-radius: 8px;
    padding: 5px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 650;
}
</style>
"""


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def process_uploaded_files(files_payload):
    loaded_sheets, loading_errors = load_excel_files(files_payload)
    concatenated_dataframe = concatenate_sheets(loaded_sheets)
    cleaned_dataframe = clean_dataframe(concatenated_dataframe)
    validation_report = validate_dataframe(cleaned_dataframe)
    costs_dataframe = extract_costs(cleaned_dataframe)
    cost_kpis = calculate_cost_kpis(costs_dataframe)

    return (
        loaded_sheets,
        loading_errors,
        cleaned_dataframe,
        validation_report,
        costs_dataframe,
        cost_kpis,
    )


def render_notice(title: str, message: str, css_class: str = "notice-card"):
    st.markdown(
        f"""
        <div class="{css_class}">
            <strong>{title}</strong><br>
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.markdown(
        """
        <div class="workspace-header">
            <h1 class="workspace-title">IVECO Protos Intelligence</h1>
            <p class="workspace-subtitle">
                Consolidation des fichiers Proto Plan, Proto 1, Proto 2 et Proto N,
                controle DAP/CID, analyse des couts et export Power BI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    with st.sidebar:
        st.title("Navigation")
        st.markdown(
            """
            **Processus**

            1. Importer les fichiers prototypes
            2. Concatener les sources Excel
            3. Extraire les variables metier
            4. Controler DAP / CID
            5. Analyser les couts
            6. Exporter vers Power BI
            """
        )

        st.divider()
        st.markdown("### Performance")
        st.caption("Les fichiers analyses sont mis en cache pour accelerer les actualisations.")

        if st.button("Vider le cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache supprime.")

        st.divider()
        st.caption("Synthese Design Prototypes")


render_header()
render_sidebar()


uploaded_files = st.file_uploader(
    "Importer Proto Plan, Proto 1, Proto 2 ou Proto N",
    type=["xlsx", "xlsm"],
    accept_multiple_files=True,
    help="Plusieurs fichiers Excel peuvent etre importes simultanement.",
)


if not uploaded_files:
    render_notice(
        "Aucun fichier importe.",
        "Selectionnez un ou plusieurs fichiers Excel pour lancer l'analyse de consolidation.",
        "status-card",
    )
    st.stop()


files_payload = [
    {"name": uploaded_file.name, "content": uploaded_file.getvalue()}
    for uploaded_file in uploaded_files
]


start_time = time.perf_counter()

with st.spinner("Lecture Excel, extraction des variables et preparation Power BI..."):
    (
        loaded_sheets,
        loading_errors,
        cleaned_df,
        validation_report,
        costs_df,
        cost_kpis,
    ) = process_uploaded_files(files_payload)

processing_time = time.perf_counter() - start_time


for loading_error in loading_errors:
    render_notice("Fichier a verifier", loading_error)


if cleaned_df.empty:
    render_notice(
        "Aucune donnee exploitable.",
        "Le fichier est vide ou ses feuilles ne contiennent pas de tableau lisible. Verifiez le classeur puis relancez l'import.",
    )
    st.stop()


render_notice(
    "Analyse terminee",
    (
        f"{len(uploaded_files)} fichier(s), {len(loaded_sheets)} feuille(s) et "
        f"{len(cleaned_df):,} enregistrement(s) consolides en {processing_time:.2f} seconde(s)."
    ),
    "success-card",
)


filtered_df = apply_filters(cleaned_df)


if filtered_df.empty:
    render_notice(
        "Aucun resultat pour ces filtres.",
        "Elargissez la selection de fichiers, feuilles ou valeurs pour afficher les donnees.",
    )
    st.stop()


filtered_ids = set(filtered_df["id_ligne"].dropna().tolist())

if not costs_df.empty and "id_ligne" in costs_df.columns:
    filtered_costs_df = costs_df[costs_df["id_ligne"].isin(filtered_ids)].copy()
else:
    filtered_costs_df = costs_df.copy()


filtered_validation_report = validate_dataframe(filtered_df)
filtered_cost_kpis = calculate_cost_kpis(filtered_costs_df)


tabs = st.tabs(
    [
        "Vue executive",
        "Analyse detaillee",
        "Donnees consolidees",
        "Qualite DAP / CID",
        "Export Power BI",
    ]
)


with tabs[0]:
    display_dashboard(
        dataframe=filtered_df,
        validation_report=filtered_validation_report,
        cost_kpis=filtered_cost_kpis,
    )


with tabs[1]:
    display_detailed_charts(dataframe=filtered_df, costs_dataframe=filtered_costs_df)


with tabs[2]:
    st.markdown('<div class="section-title">Donnees consolidees</div>', unsafe_allow_html=True)
    st.dataframe(filtered_df, use_container_width=True, height=650, hide_index=True)


with tabs[3]:
    st.markdown('<div class="section-title">Controle qualite DAP / CID</div>', unsafe_allow_html=True)
    report = filtered_validation_report
    quality_columns = st.columns(5)

    quality_columns[0].metric("Enregistrements", report["total_rows"])
    quality_columns[1].metric("Doublons", report["duplicate_rows"])
    quality_columns[2].metric("Cellules vides", report["missing_cells"])
    quality_columns[3].metric("Valeurs negatives", report["negative_values"])
    quality_columns[4].metric("Score qualite", f"{report['quality_score']:.1f} %")

    if report["issues"].empty:
        render_notice(
            "Controle valide",
            "Aucune anomalie principale detectee sur la selection active.",
            "success-card",
        )
    else:
        render_notice(
            "Verification necessaire",
            f"{len(report['issues']):,} point(s) a verifier avant validation DAP / CID.",
        )
        st.dataframe(report["issues"], use_container_width=True, height=550, hide_index=True)


with tabs[4]:
    st.markdown('<div class="section-title">Preparation Power BI</div>', unsafe_allow_html=True)

    csv_data = filtered_df.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(
        label="Telecharger les donnees consolidees",
        data=csv_data,
        file_name="iveco_protos_consolides.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if not filtered_costs_df.empty:
        costs_csv = filtered_costs_df.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="Telecharger l'analyse des couts",
            data=costs_csv,
            file_name="iveco_protos_couts.csv",
            mime="text/csv",
            use_container_width=True,
        )

    issues_dataframe = filtered_validation_report["issues"]

    if not issues_dataframe.empty:
        issues_csv = issues_dataframe.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="Telecharger les controles DAP CID",
            data=issues_csv,
            file_name="iveco_protos_controles_dap_cid.csv",
            mime="text/csv",
            use_container_width=True,
        )

    render_notice(
        "Modele Power BI",
        "Importez les CSV avec le separateur point-virgule. Les champs metier principaux sont systeme, composant, prototype, quantite, prix_piece_ke et cout_detecte.",
        "status-card",
    )

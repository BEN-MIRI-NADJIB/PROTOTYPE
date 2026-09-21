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
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
.stApp {
    background: linear-gradient(
        180deg,
        #f7f9fc 0%,
        #ffffff 45%,
        #f5f7fa 100%
    );
}

[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(12px);
}

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #002b49 0%,
        #004f71 55%,
        #0078a8 100%
    );
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: white;
}

[data-testid="stSidebar"] input {
    color: #111827;
}

[data-testid="stMetric"] {
    background: linear-gradient(
        135deg,
        #ffffff,
        #f0f7fc
    );
    border: 1px solid rgba(0, 78, 113, 0.14);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 10px 30px rgba(0, 48, 73, 0.08);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    animation: fadeInUp 0.6s ease both;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-5px);
    box-shadow: 0 16px 35px rgba(0, 48, 73, 0.15);
}

[data-testid="stMetricValue"] {
    color: #004f71;
    font-weight: 750;
}

.hero-container {
    position: relative;
    overflow: hidden;
    border-radius: 25px;
    padding: 32px;
    margin-bottom: 24px;
    color: white;
    background: linear-gradient(
        125deg,
        #002b49 0%,
        #00587a 55%,
        #00a3c7 100%
    );
    box-shadow: 0 20px 50px rgba(0, 43, 73, 0.22);
    animation: fadeInDown 0.7s ease both;
}

.hero-container::before {
    content: "";
    position: absolute;
    width: 240px;
    height: 240px;
    border-radius: 50%;
    right: -60px;
    top: -90px;
    background: rgba(255, 255, 255, 0.10);
    animation: floatingCircle 5s ease-in-out infinite;
}

.hero-title {
    position: relative;
    z-index: 2;
    margin: 0;
    font-size: 34px;
    font-weight: 800;
}

.hero-subtitle {
    position: relative;
    z-index: 2;
    margin: 10px 0 0 0;
    font-size: 16px;
    opacity: 0.90;
}

.status-card,
.success-card {
    border-radius: 14px;
    padding: 15px 18px;
    margin: 12px 0;
    box-shadow: 0 8px 25px rgba(0, 43, 73, 0.08);
    animation: fadeInUp 0.5s ease both;
}

.status-card {
    background: white;
    border-left: 5px solid #00a3c7;
}

.success-card {
    background: linear-gradient(
        135deg,
        #e7f9f0,
        #f5fffa
    );
    border: 1px solid rgba(22, 163, 74, 0.18);
    border-left: 5px solid #16a34a;
    color: #14532d;
}

.section-title {
    color: #003b5c;
    font-size: 23px;
    font-weight: 760;
    margin: 12px 0;
}

.stButton > button,
.stDownloadButton > button {
    border: 0;
    border-radius: 12px;
    color: white;
    font-weight: 650;
    background: linear-gradient(
        100deg,
        #004f71,
        #008eb4
    );
    box-shadow: 0 8px 20px rgba(0, 79, 113, 0.18);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 25px rgba(0, 79, 113, 0.28);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(241, 245, 249, 0.90);
    border-radius: 15px;
    padding: 7px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 16px;
    font-weight: 650;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(18px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-15px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes floatingCircle {
    0%, 100% {
        transform: translateY(0) scale(1);
    }

    50% {
        transform: translateY(14px) scale(1.06);
    }
}
</style>
"""


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def process_uploaded_files(files_payload):
    loaded_sheets, loading_errors = load_excel_files(
        files_payload
    )

    concatenated_dataframe = concatenate_sheets(
        loaded_sheets
    )

    cleaned_dataframe = clean_dataframe(
        concatenated_dataframe
    )

    validation_report = validate_dataframe(
        cleaned_dataframe
    )

    costs_dataframe = extract_costs(
        cleaned_dataframe
    )

    cost_kpis = calculate_cost_kpis(
        costs_dataframe
    )

    return (
        loaded_sheets,
        loading_errors,
        cleaned_dataframe,
        validation_report,
        costs_dataframe,
        cost_kpis,
    )


def render_header():
    st.markdown(
        """
        <div class="hero-container">
            <h1 class="hero-title">
                IVECO Protos Intelligence
            </h1>
            <p class="hero-subtitle">
                Centralisation, harmonisation, contrôle et analyse
                intelligente des prototypes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    with st.sidebar:
        st.title("🚌 Navigation")

        st.markdown(
            """
            **Objectif du POC**

            1. Importer les fichiers prototypes
            2. Concaténer les différentes sources
            3. Harmoniser les données
            4. Vérifier les anomalies
            5. Analyser les coûts
            6. Exporter vers Power BI
            """
        )

        st.divider()

        st.markdown("### Performances")

        st.caption(
            "Les fichiers analysés sont mis en cache "
            "pour accélérer les actualisations."
        )

        if st.button(
            "Vider le cache",
            use_container_width=True,
        ):
            st.cache_data.clear()
            st.success("Cache supprimé.")

        st.divider()

        st.caption(
            "POC Prototype Design et Coûts"
        )


render_header()
render_sidebar()


uploaded_files = st.file_uploader(
    "Importer Proto Plan, Proto 1, Proto 2 ou Proto N",
    type=["xlsx", "xlsm"],
    accept_multiple_files=True,
    help=(
        "Plusieurs fichiers peuvent être importés "
        "simultanément."
    ),
)


if not uploaded_files:
    st.markdown(
        """
        <div class="status-card">
            <strong>Aucun fichier importé.</strong><br>
            Sélectionnez un ou plusieurs fichiers Excel
            pour lancer automatiquement l'analyse.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


files_payload = [
    {
        "name": uploaded_file.name,
        "content": uploaded_file.getvalue(),
    }
    for uploaded_file in uploaded_files
]


start_time = time.perf_counter()


with st.spinner(
    "Analyse, harmonisation et préparation "
    "des visualisations..."
):
    (
        loaded_sheets,
        loading_errors,
        cleaned_df,
        validation_report,
        costs_df,
        cost_kpis,
    ) = process_uploaded_files(files_payload)


processing_time = time.perf_counter() - start_time


for error in loading_errors:
    st.warning(error)


if cleaned_df.empty:
    st.error(
        "Aucune donnée exploitable n'a été trouvée."
    )

    st.stop()


st.markdown(
    f"""
    <div class="success-card">
        <strong>
            Analyse terminée en {processing_time:.2f} seconde(s).
        </strong>
        <br>
        {len(uploaded_files)} fichier(s),
        {len(loaded_sheets)} feuille(s) et
        {len(cleaned_df):,} ligne(s) disponibles.
    </div>
    """,
    unsafe_allow_html=True,
)


filtered_df = apply_filters(
    cleaned_df
)


if filtered_df.empty:
    st.warning(
        "Aucune ligne ne correspond aux filtres sélectionnés."
    )

    st.stop()


filtered_ids = set(
    filtered_df["id_ligne"]
    .dropna()
    .tolist()
)


if (
    not costs_df.empty
    and "id_ligne" in costs_df.columns
):
    filtered_costs_df = costs_df[
        costs_df["id_ligne"].isin(filtered_ids)
    ].copy()
else:
    filtered_costs_df = costs_df.copy()


filtered_validation_report = validate_dataframe(
    filtered_df
)

filtered_cost_kpis = calculate_cost_kpis(
    filtered_costs_df
)


tabs = st.tabs(
    [
        "📊 Vue exécutive",
        "📈 Analyse détaillée",
        "📋 Données consolidées",
        "✅ Qualité DAP / CID",
        "📤 Export Power BI",
    ]
)


with tabs[0]:
    display_dashboard(
        dataframe=filtered_df,
        validation_report=filtered_validation_report,
        cost_kpis=filtered_cost_kpis,
    )


with tabs[1]:
    display_detailed_charts(
        dataframe=filtered_df,
        costs_dataframe=filtered_costs_df,
    )


with tabs[2]:
    st.markdown(
        (
            '<div class="section-title">'
            "Données consolidées"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=650,
        hide_index=True,
    )


with tabs[3]:
    st.markdown(
        (
            '<div class="section-title">'
            "Contrôle qualité DAP / CID"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    report = filtered_validation_report

    quality_columns = st.columns(5)

    quality_columns[0].metric(
        "Lignes analysées",
        report["total_rows"],
    )

    quality_columns[1].metric(
        "Doublons",
        report["duplicate_rows"],
    )

    quality_columns[2].metric(
        "Cellules vides",
        report["missing_cells"],
    )

    quality_columns[3].metric(
        "Valeurs négatives",
        report["negative_values"],
    )

    quality_columns[4].metric(
        "Score qualité",
        f"{report['quality_score']:.1f} %",
    )

    if report["issues"].empty:
        st.success(
            "Aucune anomalie principale détectée."
        )
    else:
        st.warning(
            f"{len(report['issues']):,} "
            "anomalie(s) détectée(s)."
        )

        st.dataframe(
            report["issues"],
            use_container_width=True,
            height=550,
            hide_index=True,
        )


with tabs[4]:
    st.markdown(
        (
            '<div class="section-title">'
            "Préparation Power BI"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    csv_data = filtered_df.to_csv(
        index=False,
        sep=";",
    ).encode("utf-8-sig")

    st.download_button(
        label="Télécharger les données consolidées",
        data=csv_data,
        file_name="iveco_protos_consolides.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if not filtered_costs_df.empty:
        costs_csv = filtered_costs_df.to_csv(
            index=False,
            sep=";",
        ).encode("utf-8-sig")

        st.download_button(
            label="Télécharger l'analyse des coûts",
            data=costs_csv,
            file_name="iveco_protos_couts.csv",
            mime="text/csv",
            use_container_width=True,
        )

    issues_dataframe = filtered_validation_report[
        "issues"
    ]

    if not issues_dataframe.empty:
        issues_csv = issues_dataframe.to_csv(
            index=False,
            sep=";",
        ).encode("utf-8-sig")

        st.download_button(
            label="Télécharger les anomalies",
            data=issues_csv,
            file_name="iveco_protos_anomalies.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.info(
        "Les fichiers CSV utilisent le séparateur "
        "point-virgule et peuvent être importés "
        "directement dans Power BI."
    )

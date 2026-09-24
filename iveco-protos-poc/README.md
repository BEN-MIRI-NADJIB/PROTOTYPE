# IVECO Protos Intelligence V2

Application Streamlit de consolidation des classeurs MASTER_SUIVI_PROTO et Follow-up_P1 à Follow-up_PN.

## Nouveautés
- séparation automatique Étude / Fabrication ;
- consolidation FT, DAP, CID, EBOM, planning, fournisseurs et coûts ;
- calcul des impacts, conséquences et score de risque ;
- tableaux dédiés Étude, Fabrication, Impacts, Coûts et Qualité ;
- export ZIP de six CSV compatibles Power BI.

## Installation Windows
```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
streamlit run app.py
```

## Test complet avec les vrais fichiers
1. Copier les fichiers `.xlsm` dans le dossier `data`.
2. Exécuter :
```powershell
pytest -q
```
3. Démarrer ensuite l'application :
```powershell
streamlit run app.py
```

## Utilisation
Importer en même temps MASTER_SUIVI_PROTO.xlsm et les fichiers Follow-up_P1.xlsm à Follow-up_PN.xlsm. Les macros ne sont pas exécutées et les fichiers importés ne sont pas modifiés.

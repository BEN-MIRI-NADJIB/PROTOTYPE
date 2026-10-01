# IVECO Protos Intelligence

Application Streamlit qui consolide `MASTER_SUIVI_PROTO.xlsm` et `Follow-up_P1.xlsm` à `Follow-up_PN.xlsm`.
Pour chaque prototype, elle sépare la **partie Étude** et la **partie Fabrication**, et montre l'**impact et les conséquences** de l'une sur l'autre.

## Comment les données sont lues
Chaque ligne FT de `FT_Impact` (ou `FT_Impact_Global`) porte les deux parties. L'application les sépare par FT :

| Partie | Colonnes exploitées |
|---|---|
| Étude | statut DMU, statut FT, DAP prévus / envoyés et semaines, CID (feuille `CID STATO N`) |
| Fabrication | statut de réception, besoin vs réception prévue (écart en jours), étape de montage, fournisseur, Plan B |
| Impact | conséquence véhicule (Prevent from Starting / Driving, debug, aucun impact), situation, score 0-100 |

- Périmètre d'un prototype : les FT marquées `X` dans `proto_impact` (les « NA to Pn » sont exclues), lignes de type `FT` uniquement (les niveaux MF, SD, SY, SS sont ignorés).
- Les feuilles non métier (KPI, historiques, macros, `Mistake Tracer`...) ne sont pas lues : chargement 3 fois plus rapide.
- FT jointes entre feuilles sur le numéro normalisé (`061321` = `61321`).

## Situations
- **Étude en risque → fabrication exposée** : DMU KO ou borderline, ou DAP en retard, alors que la fabrication dépend de la FT.
- **Étude et fabrication en difficulté** : double exposition.
- **Risque fabrication seul** : l'étude ne bloque pas, la réception est en retard ou manquante.
- **Maîtrisé** / **Non suivi** (aucun statut renseigné).

Score : points du statut le plus mauvais, plus étape critique, absence de Plan B, écart de plus de 30 jours, gravité de la conséquence véhicule et urgence (besoin sous 28 jours).

## Installation (Windows)
```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
streamlit run app.py
```

## Tests
Copier les `.xlsm` dans `data/` (ignorés par Git), puis :
```powershell
pytest -q
```
Sans fichiers, le test sur les vrais classeurs est ignoré, les 7 autres tournent sur des classeurs synthétiques.

## Onglets
Synthèse · Par prototype · Impact et conséquences (diagramme de flux Étude → Situation → Conséquence) · Étude · Fabrication · Planning MASTER · Qualité des données · Données et export (ZIP de 5 CSV pour Power BI).

# Pipeline Automatisé

Un pipeline de données automatisé qui récupère les prévisions météo via l'API Open-Meteo, transforme les données, les stocke en Parquet, et envoie des alertes si des conditions sont remplies.

**Compétences démontrées** : Automatisation, APIs REST, scheduling, data engineering, GitHub Actions

![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Architecture

```
┌─────────────┐     ┌───────────┐     ┌────────┐     ┌─────────┐
│  Open-Meteo │────▶│ Transform │────▶│  Load  │────▶│  Alert  │
│     API     │     │  (clean)  │     │(Parquet)│    │(Slack/  │
└─────────────┘     └───────────┘     └────────┘     │Discord) │
       ▲                                            └─────────┘
       │                                                  
       └────────────── GitHub Actions ─────────────────────┘
                      (cron: 7h UTC daily)
```

---

## Quick Start

```bash
# 1. Cloner et installer
cd pipeline-automatise
make setup

# 2. Configurer (optionnel)
cp .env.example .env
# Éditer .env avec vos paramètres

# 3. Lancer le pipeline
make run

# 4. Mode dry-run (test sans sauvegarde ni alerte)
make run-dry
```

---

## Fonctionnalités

### Source de données
- **API Open-Meteo** : gratuite, sans authentification
- Données : température max/min, précipitations, vitesse du vent
- Prévisions sur 7 jours

### Transformation
- Nettoyage des données (valeurs nulles, doublons)
- Enrichissement (température moyenne, catégories)
- Validation (plausibilité des valeurs)

### Stockage
- Format Parquet (compressé, efficace)
- Historique dans `data/archive/`

### Alertes configurables
- Température > seuil (chaud)
- Température < seuil (froid)
- Précipitations > seuil
- Vent > seuil
- Données obsolètes

### Notifications
- Console (par défaut)
- Slack (webhook)
- Discord (webhook)

---

## Configuration

Variables d'environnement (`.env`) :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `LATITUDE` | Latitude du lieu | 48.8566 |
| `LONGITUDE` | Longitude du lieu | 2.3522 |
| `LOCATION_NAME` | Nom du lieu | Paris |
| `TEMP_MAX_THRESHOLD` | Alerte si temp > X | 35.0 |
| `TEMP_MIN_THRESHOLD` | Alerte si temp < X | -10.0 |
| `PRECIPITATION_THRESHOLD` | Alerte si précip > X mm | 50.0 |
| `WIND_SPEED_THRESHOLD` | Alerte si vent > X km/h | 100.0 |
| `ALERT_ENABLED` | Activer les alertes | true |
| `SLACK_WEBHOOK_URL` | Webhook Slack | - |
| `DISCORD_WEBHOOK_URL` | Webhook Discord | - |

---

## Structure du projet

```
pipeline-automatise/
├── src/
│   ├── main.py              # Point d'entrée
│   ├── config/
│   │   └── settings.py      # Configuration (pydantic-settings)
│   ├── extract/
│   │   └── api_client.py    # Client Open-Meteo
│   ├── transform/
│   │   └── processors.py    # Transformation des données
│   ├── load/
│   │   └── storage.py       # Stockage Parquet
│   ├── alerts/
│   │   ├── conditions.py    # Conditions d'alerte
│   │   └── notifiers.py     # Notifications
│   └── utils/
│       └── logging.py       # Configuration logging
├── tests/
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_alerts.py
├── data/
│   ├── raw/                 # Données brutes
│   ├── processed/           # Données transformées
│   └── archive/             # Historique
├── .github/workflows/
│   ├── run_pipeline.yml     # Pipeline quotidien
│   └── test.yml             # Tests CI
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Commandes

```bash
make setup      # Installer les dépendances
make run        # Lancer le pipeline
make run-dry    # Lancer sans sauvegarde ni alerte réelle
make test       # Lancer les tests
make test-cov   # Tests avec couverture
make lint       # Vérifier le code
make lint-fix   # Corriger automatiquement
make clean      # Nettoyer les fichiers temporaires
```

---

## Personnalisation

### Changer la source de données

1. Créer un nouveau client dans `src/extract/`
2. Implémenter la méthode `fetch_*()` qui retourne un dict
3. Adapter `parse_*_response()` pour convertir en DataFrame

### Ajouter une condition d'alerte

```python
from src.alerts.conditions import AlertCondition, AlertResult

class CustomCondition(AlertCondition):
    def __init__(self, name: str):
        super().__init__(name, severity="warning")

    def check(self, df: pl.DataFrame) -> AlertResult:
        # Votre logique ici
        return AlertResult(
            triggered=True/False,
            condition_name=self.name,
            message="Description",
            severity=self.severity,
        )
```

### Ajouter un canal de notification

```python
from src.alerts.notifiers import Notifier

class EmailNotifier(Notifier):
    def send(self, results: list[AlertResult], location: str) -> bool:
        # Votre logique d'envoi
        return True
```

---

## Déploiement GitHub Actions

### 1. Configurer les secrets

Dans votre repo GitHub : Settings > Secrets and variables > Actions

Secrets recommandés :
- `LATITUDE` / `LONGITUDE` / `LOCATION_NAME`
- `SLACK_WEBHOOK_URL` (optionnel)
- `DISCORD_WEBHOOK_URL` (optionnel)

### 2. Activer les workflows

Les workflows sont automatiquement activés. Pour tester manuellement :
1. Aller dans Actions
2. Sélectionner "Run Data Pipeline"
3. Cliquer "Run workflow"

### 3. Fréquence

Par défaut : tous les jours à 7h UTC. Modifier le cron dans `.github/workflows/run_pipeline.yml` :

```yaml
on:
  schedule:
    - cron: '0 7 * * *'  # Modifiez ici
```

---

## Tests

```bash
# Tous les tests
make test

# Un fichier spécifique
uv run pytest tests/test_transform.py -v

# Un test spécifique
uv run pytest tests/test_transform.py::TestValidateData::test_validate_valid_data -v

# Avec couverture
make test-cov
```

---

## Crédits

- Données : [Open-Meteo](https://open-meteo.com/) (CC-BY 4.0)
- API : gratuite, sans authentification requise

---

## License

MIT

# Configuration des Secrets GitHub

Ce guide explique comment configurer les secrets pour le pipeline GitHub Actions.

## Étape 1 : Accéder aux secrets

1. Allez sur votre repository GitHub
2. Cliquez sur **Settings** (Paramètres)
3. Dans le menu de gauche, cliquez sur **Secrets and variables** > **Actions**
4. Cliquez sur **New repository secret**

## Étape 2 : Ajouter les secrets requis

### Secrets de localisation (obligatoires)

| Nom | Valeur | Description |
|-----|--------|-------------|
| `LATITUDE` | `48.8566` | Latitude du lieu à surveiller |
| `LONGITUDE` | `2.3522` | Longitude du lieu |
| `LOCATION_NAME` | `Paris` | Nom affiché dans les alertes |

### Secrets de seuils d'alerte (optionnels)

| Nom | Valeur par défaut | Description |
|-----|-------------------|-------------|
| `TEMP_MAX_THRESHOLD` | `35` | Alerte si température max dépasse (°C) |
| `TEMP_MIN_THRESHOLD` | `-10` | Alerte si température min descend sous (°C) |
| `PRECIPITATION_THRESHOLD` | `50` | Alerte si précipitations dépassent (mm) |
| `WIND_SPEED_THRESHOLD` | `100` | Alerte si vent dépasse (km/h) |

### Secrets de notification (optionnels)

| Nom | Comment obtenir |
|-----|-----------------|
| `SLACK_WEBHOOK_URL` | Voir section Slack ci-dessous |
| `DISCORD_WEBHOOK_URL` | Voir section Discord ci-dessous |

## Étape 3 : Configurer Slack (optionnel)

1. Allez sur https://api.slack.com/apps
2. Créez une nouvelle app ou utilisez une existante
3. Activez **Incoming Webhooks**
4. Cliquez sur **Add New Webhook to Workspace**
5. Sélectionnez le channel où envoyer les alertes
6. Copiez l'URL du webhook (format: `https://hooks.slack.com/services/...`)
7. Ajoutez-la comme secret `SLACK_WEBHOOK_URL`

## Étape 4 : Configurer Discord (optionnel)

1. Dans Discord, allez dans les paramètres du channel
2. Cliquez sur **Intégrations** > **Webhooks**
3. Cliquez sur **Nouveau webhook**
4. Donnez un nom et une image (optionnel)
5. Cliquez sur **Copier l'URL du webhook**
6. Ajoutez-la comme secret `DISCORD_WEBHOOK_URL`

## Étape 5 : Tester le workflow

1. Allez dans l'onglet **Actions** de votre repo
2. Sélectionnez **Run Data Pipeline**
3. Cliquez sur **Run workflow** > **Run workflow**
4. Vérifiez les logs pour confirmer que tout fonctionne

## Exemple de configuration complète

Pour un pipeline surveillant Lyon avec alertes Slack :

```
LATITUDE=45.7642
LONGITUDE=4.8357
LOCATION_NAME=Lyon
TEMP_MAX_THRESHOLD=32
TEMP_MIN_THRESHOLD=-5
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/TXXXX/BXXXX/xxxxx
```

## Sécurité

- **Ne jamais** commiter les secrets dans le code
- Les secrets sont chiffrés par GitHub
- Seuls les maintainers du repo peuvent voir/modifier les secrets
- Les logs masquent automatiquement les valeurs des secrets

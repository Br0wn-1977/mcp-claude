# 🔍 MCP Veille V3

Système de veille technologique automatisé basé sur le protocole MCP (Model Context Protocol) d'Anthropic.

![Version](https://img.shields.io/badge/version-3.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![MCP](https://img.shields.io/badge/MCP-1.0+-purple)

## 📋 Description

MCP Veille V3 permet de surveiller l'actualité technologique via deux interfaces complémentaires :
- **Claude Desktop** : Interaction en langage naturel pour lancer des veilles et analyses
- **Dashboard Streamlit** : Interface web pour visualiser et gérer les données

Le système collecte des articles depuis NewsAPI et 17 flux RSS, permet des analyses IA à la demande, et offre une gestion complète des favoris avec export Markdown.

## ✨ Fonctionnalités

### Collecte d'information
- 🎯 **6 thématiques préconfigurées** (3 IA + 3 Professionnel)
- 📡 **17 flux RSS** répartis en 5 catégories
- 🔍 **Recherche libre** sur n'importe quel sujet
- 🌐 **Support multilingue** (français, anglais, ou toutes langues)

### Analyse et rapports
- 🤖 **Analyse Claude** à la demande (synthèse, points clés, recommandations)
- 📄 **Génération de rapports** structurés

### Gestion des favoris
- ⭐ Sauvegarde d'articles avec tags
- 📥 **Export Markdown** des favoris
- ☆/⭐ Indicateur visuel (étoile vide/pleine)

### Dashboard
- 📊 Statistiques d'utilisation
- 📜 Historique des recherches avec filtres
- 🗑️ Suppression d'historiques et rapports

## 🚀 Installation rapide

### Prérequis
- Python 3.10+
- Claude Desktop
- Clés API : [NewsAPI](https://newsapi.org/) et [Anthropic](https://console.anthropic.com/)

### Étapes

```bash
# 1. Créer l'environnement virtuel
python -m venv venv

# 2. Activer l'environnement
# Windows PowerShell :
.\venv\Scripts\Activate.ps1

# 3. Installer les dépendances
pip install mcp python-dotenv requests feedparser anthropic streamlit pandas
```

### Configuration

1. Créer le fichier `.env` :
```env
NEWS_API_KEY=votre_cle_newsapi
ANTHROPIC_API_KEY=votre_cle_anthropic
```

2. Configurer Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`) :
```json
{
  "mcpServers": {
    "veille-system": {
      "command": "C:\\chemin\\vers\\projet\\venv\\Scripts\\python.exe",
      "args": ["C:\\chemin\\vers\\projet\\src\\veille_server.py"],
      "env": {"PYTHONPATH": "C:\\chemin\\vers\\projet"}
    }
  }
}
```

3. Redémarrer Claude Desktop

### Lancer le Dashboard

```bash
streamlit run src/dashboard.py
```

## 💬 Utilisation avec Claude Desktop

### Commandes principales

| Action | Exemple de commande |
|--------|---------------------|
| Voir les thématiques | "Quelles thématiques sont disponibles ?" |
| Veille thématique | "Lance une veille sur Claude & Anthropic" |
| Veille RSS | "Collecte les flux RSS des 3 derniers jours" |
| Recherche libre | "Cherche des news sur quantum computing" |
| Analyse | "Analyse les résultats" |
| Rapport | "Génère un rapport complet" |
| Favoris | "Ajoute l'article 1 à mes favoris" |

### Thématiques disponibles

**Bloc IA :**
- Claude & Anthropic
- Écosystème LLM
- IA Europe & Réglementation

**Bloc Professionnel :**
- HR Tech & Formation
- Agents IA & Automatisation
- Open Source & Outils Dev

## 📁 Structure du projet

```
MCP-Veille-V3/
├── .env                    # Clés API (non versionné)
├── README.md               # Ce fichier
├── CLAUDE.md               # Guide pour Claude Code
├── DOCUMENTATION.md        # Documentation complète
├── RECAP_FONCTIONNALITES.md # Tableau récapitulatif
│
├── src/
│   ├── veille_server.py    # Serveur MCP (9 outils)
│   └── dashboard.py        # Dashboard Streamlit
│
├── data/
│   └── veille.db           # Base SQLite
│
├── tests/
│   └── test_server.py      # Tests du serveur
│
└── venv/                   # Environnement Python
```

## 🛠️ Outils MCP

| Outil | Description |
|-------|-------------|
| `rechercher_actualites` | Recherche libre NewsAPI (param `langue`: fr/en/all) |
| `lancer_veille_thematique` | Veille sur thématique préconfigurée (param `langue`) |
| `voir_thematiques` | Liste des thématiques |
| `lancer_veille_rss` | Collecte flux RSS |
| `analyser_resultats` | Analyse Claude |
| `generer_rapport` | Création de rapport |
| `ajouter_favori` | Ajout aux favoris |
| `lister_favoris` | Liste des favoris |
| `supprimer_favori` | Suppression de favori |

## 📡 Sources RSS (17 flux)

| Catégorie | Sources |
|-----------|---------|
| Actu News tech (4) | BDM, Siècle Digital, The Gradient, Developpez |
| IA & Acteurs majeurs (4) | Google AI Blog, OpenAI Blog, DeepMind, AI News |
| Développeur & Open Source (3) | GitHub Blog, Hugging Face Blog, Ars Technica |
| Microsoft (3) | MS Azure, MS Foundry, MS Power Platform |
| Réglementation (3) | EU AI Act News, APD Belgique, Village de la Justice |

## 📅 Séquencement hebdomadaire suggéré

| Jour | Activité | Durée |
|------|----------|-------|
| Lundi | Veille RSS | 15-20 min |
| Mardi | Bloc IA (3 thématiques) | 30-45 min |
| Mercredi | Bloc PRO (3 thématiques) | 30-45 min |
| Jeudi | Exploration libre | 15-60 min |
| Vendredi | Consolidation dashboard | 20-30 min |

## 🔧 Personnalisation

### Ajouter une thématique

Dans `src/veille_server.py`, ajouter au dictionnaire `THEMATIQUES` :

```python
"Nouvelle Thématique": {
    "description": "Description",
    "keywords": ["mot-clé 1", "mot-clé 2"],
    "categorie": "IA"  # ou "PRO"
},
```

### Ajouter un flux RSS

Dans `src/veille_server.py`, ajouter au dictionnaire `RSS_FEEDS` :

```python
"Catégorie": [
    {"name": "Nom", "url": "https://..."},
],
```

## 🐛 Dépannage

| Problème | Solution |
|----------|----------|
| "Server disconnected" | Vérifier le chemin Python dans la config Claude Desktop |
| "Module not found" | Réinstaller les dépendances dans le venv |
| Colonnes manquantes | Supprimer `data/veille.db` et redémarrer |

Logs serveur : `%APPDATA%\Claude\logs\mcp-server-veille-system.log`

## 📚 Documentation

- [DOCUMENTATION.md](DOCUMENTATION.md) — Documentation complète
- [RECAP_FONCTIONNALITES.md](RECAP_FONCTIONNALITES.md) — Tableau récapitulatif

## 📄 Licence

Projet personnel - Usage libre

---

*MCP Veille V3 - Mars 2026*

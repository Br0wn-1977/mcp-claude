# MCP Veille V3 - Documentation Complète

## 📋 Table des matières

1. [Présentation du projet](#présentation-du-projet)
2. [Architecture technique](#architecture-technique)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Outils MCP disponibles](#outils-mcp-disponibles)
6. [Thématiques de veille](#thématiques-de-veille)
7. [Flux RSS configurés](#flux-rss-configurés)
8. [Dashboard Streamlit](#dashboard-streamlit)
9. [Base de données](#base-de-données)
10. [Guide d'utilisation](#guide-dutilisation)
11. [Séquencement hebdomadaire recommandé](#séquencement-hebdomadaire-recommandé)
12. [Personnalisation](#personnalisation)
13. [Dépannage](#dépannage)
14. [Fichiers du projet](#fichiers-du-projet)

---

## Présentation du projet

### Objectif

MCP Veille V3 est un système de veille technologique automatisé basé sur le protocole MCP (Model Context Protocol) d'Anthropic. Il permet de surveiller l'actualité technologique à travers plusieurs sources (NewsAPI, flux RSS) et d'interagir avec le système en langage naturel via Claude Desktop.

### Fonctionnalités principales

- **Veille thématique** : Surveillance automatisée de 6 domaines technologiques préconfigurés
- **Veille RSS** : Collecte d'articles depuis 19 flux RSS de sources de qualité
- **Recherche libre** : Exploration de n'importe quel sujet via NewsAPI
- **Analyse IA** : Synthèse et recommandations générées par Claude à la demande
- **Gestion des favoris** : Sauvegarde et export des articles importants
- **Génération de rapports** : Création de rapports structurés avec analyse
- **Dashboard web** : Interface visuelle pour consulter et gérer les données

### Interfaces disponibles

| Interface | Usage | Accès |
|-----------|-------|-------|
| Claude Desktop | Interaction en langage naturel | Application desktop |
| Dashboard Streamlit | Visualisation et gestion | http://localhost:8501 |

---

## Architecture technique

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        UTILISATEUR                               │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                      ▼                       ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│      Claude Desktop         │   │    Dashboard Streamlit      │
│   (Langage naturel)         │   │   (Interface web)           │
└─────────────────────┬───────┘   └─────────────────┬───────────┘
                      │                             │
                      ▼                             │
┌─────────────────────────────┐                     │
│     Serveur MCP             │                     │
│   (veille_server.py)        │                     │
│                             │                     │
│  ┌────────────────────────┐ │                     │
│  │ 9 Outils MCP           │ │                     │
│  │ - rechercher_actualites│ │                     │
│  │ - lancer_veille_themat.│ │                     │
│  │ - lancer_veille_rss    │ │                     │
│  │ - analyser_resultats   │ │                     │
│  │ - generer_rapport      │ │                     │
│  │ - ajouter_favori       │ │                     │
│  │ - lister_favoris       │ │                     │
│  │ - supprimer_favori     │ │                     │
│  │ - voir_thematiques     │ │                     │
│  └────────────────────────┘ │                     │
└─────────────────────┬───────┘                     │
                      │                             │
                      ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Base de données SQLite                        │
│                      (data/veille.db)                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────────────┐  ┌───────────────┐  │
│  │   favoris    │  │ historique_recherches│  │   rapports    │  │
│  └──────────────┘  └──────────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APIs Externes                               │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   NewsAPI    │  │  Flux RSS    │  │   Anthropic API       │  │
│  │  (articles)  │  │ (19 sources) │  │   (analyse Claude)    │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Technologies utilisées

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Serveur MCP | Python + MCP SDK | >= 1.0.0 |
| Dashboard | Streamlit | >= 1.28.0 |
| Base de données | SQLite | 3.x |
| Parser RSS | feedparser | >= 6.0.0 |
| Client IA | anthropic | >= 0.18.0 |
| API News | NewsAPI | v2 |

---

## Installation

### Prérequis

- Python 3.10 ou supérieur
- Claude Desktop installé
- Compte NewsAPI (clé API gratuite)
- Compte Anthropic (clé API)

### Étape 1 : Cloner/Créer le projet

```powershell
# Créer le dossier du projet
mkdir "C:\Users\<username>\MCP-Veille-V3"
cd "C:\Users\<username>\MCP-Veille-V3"

# Créer la structure
mkdir src, data, tests
```

### Étape 2 : Environnement virtuel

```powershell
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement
.\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install mcp python-dotenv requests feedparser anthropic streamlit pandas
```

### Étape 3 : Configuration des clés API

Créer un fichier `.env` à la racine du projet :

```env
NEWS_API_KEY=votre_cle_newsapi
ANTHROPIC_API_KEY=votre_cle_anthropic
```

### Étape 4 : Configuration de Claude Desktop

Modifier le fichier `%APPDATA%\Claude\claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "veille-system": {
      "command": "C:\\Users\\<username>\\MCP-Veille-V3\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\<username>\\MCP-Veille-V3\\src\\veille_server.py"],
      "env": {
        "PYTHONPATH": "C:\\Users\\<username>\\MCP-Veille-V3"
      }
    }
  }
}
```

> ⚠️ **Important** : Remplacez `<username>` par votre nom d'utilisateur Windows et adaptez les chemins à votre installation.

### Étape 5 : Redémarrer Claude Desktop

Fermez complètement Claude Desktop et relancez-le pour charger la nouvelle configuration.

### Étape 6 : Lancer le Dashboard

```powershell
cd "C:\Users\<username>\MCP-Veille-V3"
.\venv\Scripts\Activate.ps1
streamlit run src/dashboard.py
```

---

## Configuration

### Variables d'environnement

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `NEWS_API_KEY` | Clé API NewsAPI pour les recherches d'articles | Oui |
| `ANTHROPIC_API_KEY` | Clé API Anthropic pour l'analyse Claude | Oui |

### Obtenir les clés API

**NewsAPI** :
1. Aller sur https://newsapi.org/
2. Créer un compte gratuit
3. Copier la clé API depuis le dashboard

**Anthropic** :
1. Aller sur https://console.anthropic.com/
2. Créer un compte
3. Générer une clé API depuis les paramètres

---

## Outils MCP disponibles

### Tableau récapitulatif

| Outil | Fonction | Paramètres |
|-------|----------|------------|
| `rechercher_actualites` | Recherche libre sur NewsAPI | sujet (requis), jours (défaut: 7), max_articles (défaut: 10), langue (défaut: "fr") |
| `lancer_veille_thematique` | Veille sur une thématique préconfigurée | thematique (requis), jours (défaut: 7), max_articles (défaut: 10), langue (défaut: "fr") |
| `voir_thematiques` | Liste les thématiques disponibles | Aucun |
| `lancer_veille_rss` | Collecte les flux RSS | jours (défaut: 3), categorie (optionnel) |
| `analyser_resultats` | Analyse Claude des derniers résultats | Aucun |
| `generer_rapport` | Crée un rapport structuré | inclure_analyse (défaut: true) |
| `ajouter_favori` | Sauvegarde un article | url, titre (requis), source, description, tags (optionnels) |
| `lister_favoris` | Affiche les favoris | limite (défaut: 20) |
| `supprimer_favori` | Retire un favori | favori_id ou url |

> **Note** : Le paramètre `langue` accepte "fr" (français), "en" (anglais), ou "all" (toutes langues).

### Détail des outils

#### rechercher_actualites

Effectue une recherche libre sur n'importe quel sujet via NewsAPI.

**Exemples d'utilisation** :
- "Cherche des actualités sur quantum computing"
- "Trouve des news sur Tesla des 3 derniers jours"
- "Recherche articles blockchain, 15 résultats max"

**Paramètres** :
- `sujet` (string, requis) : Mots-clés de recherche
- `jours` (integer, défaut: 7) : Période de recherche en jours (1-30)
- `max_articles` (integer, défaut: 10) : Nombre maximum d'articles (1-100)
- `langue` (string, défaut: "fr") : Langue des articles ("fr", "en", "all")

---

#### lancer_veille_thematique

Lance une veille sur une des 6 thématiques préconfigurées avec des mots-clés optimisés.

**Exemples d'utilisation** :
- "Lance une veille sur Claude & Anthropic"
- "Veille thématique Écosystème LLM sur 14 jours"
- "Surveille HR Tech & Formation"

**Paramètres** :
- `thematique` (string, requis) : Nom exact de la thématique
- `jours` (integer, défaut: 7) : Période de recherche (1-30)
- `max_articles` (integer, défaut: 10) : Nombre maximum d'articles (1-100)
- `langue` (string, défaut: "fr") : Langue des articles ("fr", "en", "all")

---

#### voir_thematiques

Affiche la liste des 6 thématiques disponibles avec leurs descriptions.

**Exemple d'utilisation** :
- "Quelles sont les thématiques disponibles ?"

---

#### lancer_veille_rss

Collecte les articles récents depuis les 19 flux RSS configurés (5 catégories).

**Exemples d'utilisation** :
- "Lance la veille RSS"
- "Collecte les flux RSS des 2 derniers jours"
- "Veille RSS catégorie Développeur"

**Paramètres** :
- `jours` (integer, défaut: 3) : Période de collecte
- `categorie` (string, optionnel) : Filtrer par catégorie RSS

---

#### analyser_resultats

Génère une analyse Claude des derniers résultats collectés (recherche, thématique ou RSS).

**Exemples d'utilisation** :
- "Analyse les résultats"
- "Fais une synthèse des articles"
- "Donne-moi les points clés"

**Sortie** :
- Synthèse générale
- Points clés
- Lectures prioritaires
- Recommandations

---

#### generer_rapport

Crée un rapport structuré avec tous les articles et optionnellement une analyse Claude.

**Exemples d'utilisation** :
- "Génère un rapport"
- "Crée un rapport complet avec analyse"
- "Rapport sans analyse"

**Paramètres** :
- `inclure_analyse` (boolean, défaut: true) : Inclure l'analyse Claude

---

#### ajouter_favori

Sauvegarde un article dans les favoris.

**Exemples d'utilisation** :
- "Ajoute le premier article à mes favoris"
- "Garde cet article"
- "Sauvegarde l'article 3 avec le tag 'important'"

**Paramètres** :
- `url` (string, requis) : URL de l'article
- `titre` (string, requis) : Titre de l'article
- `source` (string, optionnel) : Source de l'article
- `description` (string, optionnel) : Description
- `tags` (string, optionnel) : Tags séparés par virgules

---

#### lister_favoris

Affiche la liste des articles favoris.

**Exemples d'utilisation** :
- "Montre mes favoris"
- "Quels articles j'ai sauvegardés ?"
- "Liste mes 10 derniers favoris"

**Paramètres** :
- `limite` (integer, défaut: 20) : Nombre maximum de favoris à afficher

---

#### supprimer_favori

Retire un article des favoris.

**Exemples d'utilisation** :
- "Supprime le favori numéro 3"
- "Retire ce favori"

**Paramètres** :
- `favori_id` (integer) : ID du favori à supprimer
- `url` (string) : URL de l'article (alternative à l'ID)

---

## Thématiques de veille

### Bloc IA (3 thématiques)

| Thématique | Description | Mots-clés |
|------------|-------------|-----------|
| **Claude & Anthropic** | Actualités Anthropic, Claude AI, protocole MCP | Anthropic Claude, Claude AI, MCP Anthropic, Claude Sonnet |
| **Écosystème LLM** | OpenAI, Google Gemini, Mistral, Meta Llama | OpenAI GPT, Google Gemini AI, Mistral AI, Meta Llama |
| **IA Europe & Réglementation** | AI Act, RGPD appliqué à l'IA, positions CNIL | AI Act Europe, RGPD intelligence artificielle, regulation AI Europe |

### Bloc Professionnel (3 thématiques)

| Thématique | Description | Mots-clés |
|------------|-------------|-----------|
| **HR Tech & Formation** | Cornerstone, LMS, talent management | Cornerstone OnDemand, HR Technology, Learning Management System |
| **Agents IA & Automatisation** | AI Agents, RAG, LangChain | AI Agents autonomous, LangChain AI, RAG retrieval augmented |
| **Open Source & Outils Dev** | Hugging Face, Open WebUI, Ollama | Hugging Face models, Open WebUI, Ollama local LLM |

---

## Flux RSS configurés (19 flux)

### Actu News tech (5 flux)

| Source | URL |
|--------|-----|
| VentureBeat | https://venturebeat.com/feed/ |
| BDM (Blog du Modérateur) | https://www.blogdumoderateur.com/feed/ |
| Siècle Digital | https://siecledigital.fr/feed/ |
| The Gradient | https://thegradient.pub/rss/ |
| Developpez | https://www.developpez.com/index/rss |

### IA & Acteurs majeurs (6 flux)

| Source | URL |
|--------|-----|
| Google AI Blog | https://blog.google/technology/ai/rss/ |
| OpenAI Blog | https://openai.com/blog/rss.xml |
| DeepMind | https://deepmind.google/blog/rss.xml |
| MIT Tech Review | https://www.technologyreview.com/feed/ |
| AI News | https://www.artificialintelligence-news.com/feed/ |
| The Verge AI | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml |

### Développeur & Open Source (3 flux)

| Source | URL |
|--------|-----|
| GitHub Blog | https://github.blog/feed/ |
| Hugging Face Blog | https://huggingface.co/blog/feed.xml |
| Ars Technica | https://feeds.arstechnica.com/arstechnica/technology-lab |

### Microsoft (3 flux)

| Source | URL |
|--------|-----|
| MS Azure | https://azure.microsoft.com/en-us/blog/feed/ |
| MS Foundry | https://devblogs.microsoft.com/foundry/feed/ |
| MS Power Platform | https://devblogs.microsoft.com/powerplatform/feed/ |

### Réglementation (2 flux)

| Source | URL |
|--------|-----|
| CNIL Actualités | https://www.cnil.fr/fr/rss.xml |
| EU AI Act News | https://artificialintelligenceact.eu/feed/ |

---

## Dashboard Streamlit

### Pages disponibles

#### 📊 Dashboard (Accueil)

Vue d'ensemble du système avec :
- Statistiques globales (favoris, recherches, rapports)
- Derniers favoris ajoutés
- Activité récente
- Liste des thématiques disponibles

#### ⭐ Favoris

Gestion complète des favoris :
- Recherche dans les favoris
- Affichage détaillé (titre, source, date, description, tags)
- Suppression de favoris
- **Export Markdown** : Téléchargement de tous les favoris au format .md

#### 📜 Historique

Suivi de toutes les recherches :
- Filtrage par type (recherche, thématique, RSS)
- Filtrage par rapport associé
- Affichage des rapports directement dans l'historique
- Ajout aux favoris depuis les rapports
- Suppression d'entrées d'historique
- Indicateur visuel des rapports associés (📄)

#### 📄 Rapports

Consultation des rapports générés :
- Liste de tous les rapports
- Onglet Articles avec ajout aux favoris
- Onglet Analyse Claude
- Onglet Contenu brut
- Suppression de rapports

### Indicateurs visuels

| Icône | Signification |
|-------|---------------|
| ⭐ | Article en favori (étoile pleine) |
| ☆ | Article non favori - cliquer pour ajouter |
| 📄 | Rapport associé disponible |
| 🔍 | Recherche libre |
| 🎯 | Veille thématique |
| 📡 | Veille RSS |

---

## Base de données

### Structure

La base de données SQLite (`data/veille.db`) contient 3 tables :

#### Table `favoris`

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Clé primaire auto-incrémentée |
| url | TEXT | URL de l'article (unique) |
| titre | TEXT | Titre de l'article |
| source | TEXT | Source de l'article |
| description | TEXT | Description/résumé |
| date_article | TEXT | Date de publication |
| date_ajout | TEXT | Date d'ajout aux favoris |
| tags | TEXT | Tags séparés par virgules |
| thematique | TEXT | Thématique associée |

#### Table `historique_recherches`

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Clé primaire auto-incrémentée |
| type | TEXT | Type de recherche (recherche, thematique, rss) |
| query | TEXT | Requête ou nom de thématique |
| date_recherche | TEXT | Date et heure de la recherche |
| nb_resultats | INTEGER | Nombre de résultats trouvés |
| parametres | TEXT | Paramètres JSON de la recherche |

#### Table `rapports`

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Clé primaire auto-incrémentée |
| type | TEXT | Type de rapport |
| titre | TEXT | Titre du rapport |
| date_creation | TEXT | Date de création |
| contenu | TEXT | Contenu complet du rapport |
| analyse | TEXT | Analyse Claude |
| metadata | TEXT | Métadonnées JSON |

---

## Guide d'utilisation

### Workflow type

```
1. Lancer une veille (thématique, RSS ou recherche libre)
         │
         ▼
2. Consulter les résultats affichés
         │
         ▼
3. (Optionnel) Demander une analyse Claude
         │
         ▼
4. (Optionnel) Générer un rapport
         │
         ▼
5. Ajouter les articles intéressants aux favoris
         │
         ▼
6. Consulter/Exporter les favoris dans le dashboard
```

### Exemples de commandes Claude Desktop

**Veille thématique** :
```
"Lance une veille sur Claude & Anthropic"
"Veille Écosystème LLM sur les 14 derniers jours, 15 articles"
```

**Veille RSS** :
```
"Collecte les flux RSS"
"Veille RSS des 2 derniers jours, catégorie Développeur"
```

**Recherche libre** :
```
"Cherche des actualités sur quantum computing"
"Recherche articles sur les semiconducteurs, 20 résultats"
```

**Analyse et rapport** :
```
"Analyse les résultats"
"Génère un rapport complet"
```

**Favoris** :
```
"Ajoute l'article 1 à mes favoris"
"Montre mes favoris"
"Supprime le favori 5"
```

---

## Séquencement hebdomadaire recommandé

### Planning type

| Jour | Activité | Durée | Actions |
|------|----------|-------|---------|
| **Lundi** | Veille RSS | 15-20 min | Collecter RSS → Analyser → Favoris |
| **Mardi** | Bloc IA | 30-45 min | 3 veilles thématiques IA → Rapport |
| **Mercredi** | Bloc PRO | 30-45 min | 3 veilles thématiques PRO → Rapport |
| **Jeudi** | Exploration | 15-60 min | Recherches libres sur sujets ponctuels |
| **Vendredi** | Consolidation | 20-30 min | Revue favoris/rapports dans dashboard |

### Détail par jour

#### Lundi - Démarrage de semaine

```
1. "Collecte les flux RSS des 3 derniers jours"
2. "Analyse les résultats"
3. Ajouter les articles importants aux favoris
```

#### Mardi - Focus IA

```
1. "Lance une veille sur Claude & Anthropic"
2. "Lance une veille sur Écosystème LLM"
3. "Lance une veille sur IA Europe & Réglementation"
4. "Génère un rapport complet"
```

#### Mercredi - Focus Professionnel

```
1. "Lance une veille sur HR Tech & Formation"
2. "Lance une veille sur Agents IA & Automatisation"
3. "Lance une veille sur Open Source & Outils Dev"
4. "Génère un rapport complet"
```

#### Jeudi - Exploration

```
- Recherches libres selon les sujets d'intérêt du moment
- Approfondissement de sujets découverts en début de semaine
```

#### Vendredi - Consolidation

```
1. Ouvrir le dashboard Streamlit
2. Consulter la page Favoris
3. Exporter les favoris en Markdown si besoin
4. Nettoyer les favoris/rapports obsolètes
```

---

## Personnalisation

### Ajouter une thématique

1. Ouvrir `src/veille_server.py`
2. Localiser le dictionnaire `THEMATIQUES` (ligne ~50)
3. Ajouter une nouvelle entrée :

```python
THEMATIQUES = {
    # ... thématiques existantes ...
    
    "Nouvelle Thématique": {
        "description": "Description de la thématique",
        "keywords": ["mot-clé 1", "mot-clé 2", "mot-clé 3"],
        "categorie": "IA"  # ou "PRO"
    },
}
```

4. Redémarrer Claude Desktop

### Ajouter un flux RSS

1. Ouvrir `src/veille_server.py`
2. Localiser le dictionnaire `RSS_FEEDS` (ligne ~85)
3. Ajouter dans une catégorie existante ou créer une nouvelle catégorie :

```python
RSS_FEEDS = {
    # ... catégories existantes ...
    
    "Nouvelle Catégorie": [
        {"name": "Nom du flux", "url": "https://example.com/feed.xml"},
    ],
}
```

4. Redémarrer Claude Desktop

### Modifier le dashboard

1. Ouvrir `src/dashboard.py`
2. Le dashboard importe automatiquement `THEMATIQUES` depuis `veille_server.py` (source unique de vérité)
3. Relancer Streamlit : `streamlit run src/dashboard.py`

---

## Dépannage

### Problème : "Server disconnected" dans Claude Desktop

**Cause** : Claude Desktop utilise le mauvais Python (global au lieu du venv)

**Solution** :
1. Vérifier le chemin Python dans `claude_desktop_config.json`
2. S'assurer que le chemin pointe vers `venv\Scripts\python.exe`
3. Redémarrer Claude Desktop

### Problème : "Module not found: mcp"

**Cause** : Les dépendances ne sont pas installées dans le bon environnement

**Solution** :
```powershell
.\venv\Scripts\Activate.ps1
pip install mcp python-dotenv requests feedparser anthropic streamlit pandas
```

### Problème : "NEWS_API_KEY manquante"

**Cause** : Le fichier `.env` n'existe pas ou ne contient pas la clé

**Solution** :
1. Créer/vérifier le fichier `.env` à la racine du projet
2. Ajouter : `NEWS_API_KEY=votre_cle_api`

### Problème : Colonnes manquantes dans la base de données

**Cause** : La structure de la BD a changé entre les versions

**Solution** :
```powershell
# Option 1 : Supprimer et recréer la BD
Remove-Item "data\veille.db"
# Puis relancer Claude Desktop

# Option 2 : Ajouter la colonne manquante
python -c "import sqlite3; conn = sqlite3.connect('data/veille.db'); conn.execute('ALTER TABLE favoris ADD COLUMN thematique TEXT'); conn.commit(); conn.close()"
```

### Problème : Le dashboard n'affiche pas les stats correctement

**Cause** : Problème de CSS avec le thème sombre

**Solution** : Vérifier que le CSS personnalisé dans `inject_custom_css()` est bien appliqué

### Consulter les logs du serveur MCP

Les logs sont disponibles dans :
```
%APPDATA%\Claude\logs\mcp-server-veille-system.log
```

---

## Fichiers du projet

### Structure du projet

```
MCP-Veille-V3/
├── .env                          # Variables d'environnement (clés API)
├── README.md                     # Documentation rapide
├── DOCUMENTATION.md              # Cette documentation complète
├── RECAP_FONCTIONNALITES.md      # Tableau récapitulatif
├── requirements.txt              # Dépendances Python
│
├── src/
│   ├── veille_server.py          # Serveur MCP principal
│   └── dashboard.py              # Dashboard Streamlit
│
├── data/
│   └── veille.db                 # Base de données SQLite
│
├── venv/                         # Environnement virtuel Python
│
└── tests/
    └── test_server.py            # Tests unitaires
```

### Description des fichiers principaux

#### veille_server.py

Serveur MCP principal qui :
- Expose les 9 outils MCP
- Gère la communication avec Claude Desktop
- Interagit avec NewsAPI et les flux RSS
- Stocke les données dans SQLite
- Appelle l'API Anthropic pour les analyses

#### dashboard.py

Interface web Streamlit qui :
- Affiche les statistiques et favoris
- Permet la navigation dans l'historique et les rapports
- Gère l'ajout/suppression des favoris
- Exporte les favoris en Markdown
- Partage la même base de données que le serveur MCP

#### veille.db

Base de données SQLite contenant :
- Les favoris sauvegardés
- L'historique des recherches
- Les rapports générés

---

## Changelog

### Version 3.1 (Janvier 2026)

- **19 flux RSS** répartis en 5 catégories (vs 7 précédemment)
- **Support multilingue** : paramètre `langue` (fr/en/all) sur les recherches
- **Validation des entrées** : jours (1-30), max_articles (1-100)
- **Refactoring THEMATIQUES** : import unique depuis veille_server.py
- **Nouvelles sources** : Siècle Digital, MIT Tech Review, AI News, The Verge AI, Ars Technica, EU AI Act News
- Correction des flux RSS cassés (Human Coders, Anthropic, MS 365)
- Meilleure gestion des erreurs (plus de `except:` silencieux)

### Version 3.0 (Décembre 2024)

- Architecture MCP complète avec 9 outils
- 6 thématiques préconfigurées (3 IA + 3 PRO)
- 7 flux RSS configurés
- Dashboard Streamlit avec 4 pages
- Export Markdown des favoris
- Indicateur visuel étoile pleine/vide pour les favoris
- Suppression possible des historiques et rapports
- Analyse Claude à la demande (économie de tokens)

---

## Support

Pour toute question ou problème :
1. Consulter la section [Dépannage](#dépannage)
2. Vérifier les logs dans `%APPDATA%\Claude\logs\`
3. S'assurer que toutes les dépendances sont installées

---

*Documentation MCP Veille V3 - Version 3.1*
*Dernière mise à jour : Janvier 2026*

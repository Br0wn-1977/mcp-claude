# 🎯 MCP Veille V3 - Système de Veille Technologique

## Vision du Projet

Ce projet implémente un **vrai serveur MCP** (Model Context Protocol) pour la veille technologique, permettant d'interagir avec Claude Desktop en langage naturel.

**Exemple de conversation possible :**
```
Toi: "Lance une veille sur Claude et Anthropic des 7 derniers jours"
Claude: [utilise l'outil MCP lancer_veille] "J'ai trouvé 12 articles..."

Toi: "Garde le premier article dans mes favoris"  
Claude: [utilise l'outil MCP ajouter_favori] "Article ajouté à vos favoris"

Toi: "Montre-moi tous mes favoris"
Claude: [lit la ressource MCP veille://favoris] "Vous avez 5 favoris..."
```

## Architecture

```
mcp-veille-v3/
├── src/
│   └── veille_server.py      # Serveur MCP principal
├── data/
│   ├── veille.db             # Base SQLite (favoris, rapports, config)
│   └── rapports/             # Rapports générés
├── tests/
│   └── test_server.py        # Tests du serveur
├── .env                      # Clés API (NEWS_API_KEY, ANTHROPIC_API_KEY)
├── requirements.txt          # Dépendances Python
└── README.md                 # Ce fichier
```

## Installation

### 1. Créer l'environnement
```powershell
cd "C:\Users\lemai\OneDrive\Bureau\VSC\MCP v2"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Installer les dépendances
```powershell
pip install -r requirements.txt
```

### 3. Configurer les clés API
Créer un fichier `.env` :
```
NEWS_API_KEY=ta_clé_newsapi
ANTHROPIC_API_KEY=ta_clé_anthropic
```

### 4. Tester le serveur
```powershell
python tests/test_server.py
```

### 5. Configurer Claude Desktop
Éditer `%APPDATA%\Claude\claude_desktop_config.json`

## Phases de Développement

- [x] Phase 1 : Socle minimal (1 outil, validation Claude Desktop)
- [ ] Phase 2 : État persistant (SQLite, favoris)
- [ ] Phase 3 : Veille complète (12 thématiques, RSS, ad-hoc)
- [ ] Phase 4 : Raffinement (prompts, stats, dashboard)

## Licence

Projet personnel - Bruno

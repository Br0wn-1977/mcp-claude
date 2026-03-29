# MCP Veille V3 - Tableau Récapitulatif des Fonctionnalités

## Outils MCP disponibles dans Claude Desktop

| Outil | Fonction | Exemple de commande | Paramètres |
|-------|----------|---------------------|------------|
| `rechercher_actualites` | Recherche libre sur n'importe quel sujet via NewsAPI | "Cherche des news sur quantum computing" | sujet (requis), jours (défaut: 7), max_articles (défaut: 10), langue (défaut: "fr") |
| `lancer_veille_thematique` | Veille sur une des 6 thématiques préconfigurées | "Lance une veille sur Claude & Anthropic" | thematique (requis), jours (défaut: 7), max_articles (défaut: 10), langue (défaut: "fr") |
| `voir_thematiques` | Affiche la liste des thématiques disponibles | "Quelles sont les thématiques disponibles ?" | Aucun |
| `lancer_veille_rss` | Collecte les articles des 17 flux RSS configurés | "Collecte les flux RSS des 3 derniers jours" | jours (défaut: 3), categorie (optionnel) |
| `analyser_resultats` | Analyse Claude des derniers résultats collectés | "Analyse les résultats" | Aucun |
| `generer_rapport` | Crée un rapport structuré sauvegardé en base | "Génère un rapport complet" | inclure_analyse (défaut: true) |
| `ajouter_favori` | Sauvegarde un article en favori | "Ajoute le premier article à mes favoris" | url, titre (requis), source, description, tags (optionnels) |
| `lister_favoris` | Affiche les articles favoris | "Montre mes favoris" | limite (défaut: 20) |
| `supprimer_favori` | Retire un article des favoris | "Supprime le favori numéro 3" | favori_id ou url |

> **Note** : Le paramètre `langue` accepte "fr" (français, défaut), "en" (anglais), ou "all" (toutes langues). Validation automatique des paramètres : jours (1-30), max_articles (1-100).

---

## Thématiques préconfigurées (NewsAPI)

| Thématique | Bloc | Description | Mots-clés utilisés |
|------------|------|-------------|-------------------|
| Claude & Anthropic | IA | Actualités Anthropic, Claude AI, protocole MCP | Anthropic Claude, Claude AI, MCP Anthropic, Claude Sonnet |
| Écosystème LLM | IA | OpenAI, Google Gemini, Mistral, Meta Llama | OpenAI GPT, Google Gemini AI, Mistral AI, Meta Llama |
| IA Europe & Réglementation | IA | AI Act, RGPD appliqué à l'IA, positions CNIL | AI Act Europe, RGPD intelligence artificielle, regulation AI Europe |
| HR Tech & Formation | PRO | Cornerstone, LMS, talent management | Cornerstone OnDemand, HR Technology, Learning Management System |
| Agents IA & Automatisation | PRO | AI Agents, RAG, LangChain, automatisation | AI Agents autonomous, LangChain AI, RAG retrieval augmented |
| Open Source & Outils Dev | PRO | Hugging Face, Open WebUI, Ollama | Hugging Face models, Open WebUI, Ollama local LLM |

---

## Flux RSS configurés (17 flux)

| Catégorie | Sources |
|-----------|---------|
| **Actu News tech** (4) | BDM, Siècle Digital, The Gradient, Developpez |
| **IA & Acteurs majeurs** (4) | Google AI Blog, OpenAI Blog, DeepMind, AI News |
| **Développeur & Open Source** (3) | GitHub Blog, Hugging Face Blog, Ars Technica |
| **Microsoft** (3) | MS Azure, MS Foundry, MS Power Platform |
| **Réglementation** (3) | EU AI Act News, APD Belgique, Village de la Justice |

---

## Pages du Dashboard Streamlit

| Page | Fonction | Actions disponibles |
|------|----------|---------------------|
| 📊 Dashboard | Vue d'ensemble | Statistiques, derniers favoris, activité récente, thématiques |
| ⭐ Favoris | Gestion des favoris | Recherche, visualisation, suppression, **export Markdown** |
| 📜 Historique | Suivi des recherches | Filtres, consultation rapports, ajout favoris, **suppression** |
| 📄 Rapports | Consultation rapports | Lecture articles, analyse Claude, ajout favoris, **suppression** |

---

## Indicateurs visuels du Dashboard

| Icône | Signification |
|-------|---------------|
| ⭐ | Article déjà en favori (étoile pleine) |
| ☆ | Article non favori - cliquer pour ajouter (étoile vide) |
| 📄 | Rapport associé disponible |
| 🔍 | Recherche libre |
| 🎯 | Veille thématique |
| 📡 | Veille RSS |
| 🗑️ | Supprimer l'élément |

---

## Architecture technique

| Composant | Fichier | Rôle |
|-----------|---------|------|
| Serveur MCP | `src/veille_server.py` | Cœur du système, expose les 9 outils MCP, gère la logique métier |
| Dashboard | `src/dashboard.py` | Interface web Streamlit pour visualisation et gestion |
| Base de données | `data/veille.db` | SQLite partagée entre serveur MCP et dashboard |
| Configuration Claude | `claude_desktop_config.json` | Connexion entre Claude Desktop et le serveur MCP |
| Variables d'env | `.env` | Clés API (NEWS_API_KEY, ANTHROPIC_API_KEY) |

---

## Séquencement hebdomadaire recommandé

| Jour | Activité | Durée estimée | Commandes type |
|------|----------|---------------|----------------|
| Lundi | Veille RSS (actualités récentes) | 15-20 min | "Collecte les flux RSS des 3 derniers jours" → "Analyse les résultats" |
| Mardi | Bloc IA (3 thématiques) | 30-45 min | Veilles sur Claude & Anthropic, Écosystème LLM, IA Europe & Réglementation |
| Mercredi | Bloc PRO (3 thématiques) | 30-45 min | Veilles sur HR Tech, Agents IA, Open Source & Outils Dev |
| Jeudi | Exploration libre | 15-60 min | Recherches libres sur sujets ponctuels |
| Vendredi | Consolidation | 20-30 min | Revue des favoris et rapports dans le dashboard, export Markdown |

---

## Commandes rapides par cas d'usage

| Je veux... | Commande Claude Desktop |
|------------|------------------------|
| Voir les thématiques disponibles | "Quelles sont les thématiques disponibles ?" |
| Lancer une veille thématique | "Lance une veille sur [nom exact de la thématique]" |
| Faire une recherche libre | "Cherche des actualités sur [sujet]" |
| Collecter les flux RSS | "Collecte les flux RSS" |
| Obtenir une synthèse IA | "Analyse les résultats" |
| Sauvegarder un article | "Ajoute l'article [numéro] à mes favoris" |
| Voir mes favoris | "Montre mes favoris" |
| Supprimer un favori | "Supprime le favori [numéro]" |
| Générer un rapport | "Génère un rapport complet" |

---

## Fonctionnalités Dashboard détaillées

### Page Favoris
- 🔍 Recherche dans les favoris (titre, description, tags)
- 📥 Export Markdown de tous les favoris
- 🗑️ Suppression individuelle
- 🏷️ Affichage des tags

### Page Historique  
- 🔽 Filtrage par type (recherche, thématique, RSS)
- 🔽 Filtrage par rapport (avec/sans rapport)
- 📄 Consultation des rapports directement dans l'historique
- ☆/⭐ Ajout aux favoris depuis les articles des rapports
- 🗑️ Suppression des entrées d'historique

### Page Rapports
- 📋 Onglet Articles : liste parsée avec ajout favoris (☆/⭐)
- 🤖 Onglet Analyse Claude : synthèse et recommandations
- 📝 Onglet Contenu brut : texte complet du rapport
- 🗑️ Suppression de rapports

---

*Document mis à jour le 29/03/2026 - MCP Veille V3.1*

# MCP Veille V3 - Tableau Récapitulatif des Fonctionnalités

## Outils MCP disponibles dans Claude Desktop

| Outil | Fonction | Exemple de commande | Paramètres |
|-------|----------|---------------------|------------|
| `rechercher_actualites` | Recherche libre sur n'importe quel sujet via NewsAPI | "Cherche des news sur quantum computing" | sujet (requis), jours (défaut: 7), max_articles (défaut: 10) |
| `lancer_veille_thematique` | Veille sur une des 6 thématiques préconfigurées | "Lance une veille sur Claude & Anthropic" | thematique (requis), jours (défaut: 7), max_articles (défaut: 10) |
| `voir_thematiques` | Affiche la liste des thématiques disponibles | "Quelles sont les thématiques disponibles ?" | Aucun |
| `lancer_veille_rss` | Collecte les articles des 7 flux RSS configurés | "Collecte les flux RSS des 3 derniers jours" | jours (défaut: 3), categorie (optionnel) |
| `analyser_resultats` | Analyse Claude des derniers résultats collectés | "Analyse les résultats" | Aucun |
| `generer_rapport` | Crée un rapport structuré sauvegardé en base | "Génère un rapport complet" | inclure_analyse (défaut: true) |
| `ajouter_favori` | Sauvegarde un article en favori | "Ajoute le premier article à mes favoris" | url, titre (requis), source, description, tags (optionnels) |
| `lister_favoris` | Affiche les articles favoris | "Montre mes favoris" | limite (défaut: 20) |
| `supprimer_favori` | Retire un article des favoris | "Supprime le favori numéro 3" | favori_id ou url |

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

## Flux RSS configurés

| Catégorie | Source | URL |
|-----------|--------|-----|
| IA & Acteurs majeurs | Hugging Face Blog | https://huggingface.co/blog/feed.xml |
| IA & Acteurs majeurs | Google AI Blog | https://blog.google/technology/ai/rss/ |
| IA & Acteurs majeurs | OpenAI Blog | https://openai.com/blog/rss.xml |
| Développeur & Open Source | Human Coders News | https://news.humancoders.com/feed |
| Développeur & Open Source | GitHub Blog | https://github.blog/feed/ |
| Développeur & Open Source | Hacker News IA | https://hnrss.org/newest?q=AI+OR+LLM+OR+Claude&points=50 |
| Réglementation | CNIL Actualités | https://www.cnil.fr/fr/rss.xml |

---

## Pages du Dashboard Streamlit

| Page | Fonction | Contenu |
|------|----------|---------|
| Dashboard | Vue d'ensemble | Statistiques globales, derniers favoris, activité récente, liste des thématiques |
| Favoris | Gestion des favoris | Liste complète avec recherche, visualisation détaillée, suppression |
| Historique | Suivi des recherches | Tableau de toutes les recherches avec filtres par type |
| Rapports | Consultation des rapports | Liste des rapports générés, visualisation du contenu et de l'analyse |
| Lancer une veille | Collecte RSS depuis le web | Interface pour lancer une collecte RSS (sans analyse Claude) |
| Flux RSS | Configuration des sources | Liste des flux configurés avec test de fonctionnement |

---

## Architecture technique

| Composant | Fichier | Rôle |
|-----------|---------|------|
| Serveur MCP | `src/veille_server.py` | Cœur du système, expose les 9 outils MCP, gère la logique métier |
| Dashboard | `src/dashboard.py` | Interface web Streamlit pour visualisation et gestion |
| Base de données | `data/veille.db` | SQLite partagée entre serveur MCP et dashboard |
| Configuration Claude | `claude_desktop_config.json` | Connexion entre Claude Desktop et le serveur MCP |
| Environnement Python | `venv/` | Environnement virtuel avec les dépendances (mcp, streamlit, feedparser, anthropic) |

---

## Séquencement hebdomadaire recommandé

| Jour | Activité | Durée estimée | Commandes type |
|------|----------|---------------|----------------|
| Lundi | Veille RSS (actualités récentes) | 15-20 min | "Collecte les flux RSS des 3 derniers jours" → "Analyse les résultats" |
| Mardi | Bloc IA (3 thématiques) | 30-45 min | Veilles sur Claude & Anthropic, Écosystème LLM, IA Europe & Réglementation |
| Mercredi | Bloc PRO (3 thématiques) | 30-45 min | Veilles sur HR Tech, Agents IA, Open Source & Outils Dev |
| Jeudi | Exploration libre | 15-60 min | Recherches libres sur sujets ponctuels |
| Vendredi | Consolidation | 20-30 min | Revue des favoris et rapports dans le dashboard |

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

*Document généré le 29/12/2025 - MCP Veille V3*

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Veille V3 is an automated technology watch system built on Anthropic's Model Context Protocol (MCP). It collects tech news from NewsAPI and RSS feeds, provides Claude-powered analysis, and manages favorites through two interfaces:
- **MCP Server** (`src/veille_server.py`) - Runs within Claude Desktop
- **Streamlit Dashboard** (`src/dashboard.py`) - Web interface sharing the same SQLite database

## Common Commands

```bash
# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install mcp python-dotenv requests feedparser anthropic streamlit pandas

# Run the Streamlit dashboard
streamlit run src/dashboard.py

# Run tests
python tests/test_server.py
```

## Architecture

### MCP Server (`src/veille_server.py`)
The server exposes 9 MCP tools to Claude Desktop:
- `rechercher_actualites` - Free-form NewsAPI search (supports `langue` param: "fr", "en", "all")
- `lancer_veille_thematique` - Search by preconfigured theme (6 themes in `THEMATIQUES` dict)
- `voir_thematiques` - List available themes
- `lancer_veille_rss` - Collect from RSS feeds (configured in `RSS_FEEDS` dict)
- `analyser_resultats` - Claude analysis of last results (uses `derniers_resultats` global)
- `generer_rapport` - Generate and save reports
- `ajouter_favori`, `lister_favoris`, `supprimer_favori` - Favorites management

Key patterns:
- Global `derniers_resultats` stores last search results for subsequent analysis
- `@server.list_tools()` and `@server.call_tool()` decorators register MCP handlers
- All data persists to `data/veille.db` (SQLite)
- Input validation via `valider_parametres()` ensures safe parameter ranges

### Streamlit Dashboard (`src/dashboard.py`)
Read-only web interface (plus favorites management) with 4 pages:
- Dashboard (stats overview)
- Favoris (with Markdown export)
- Historique (search history with linked reports)
- Rapports (view generated reports, add articles to favorites)

The dashboard parses report content with `parse_articles_from_rapport()` to extract individual articles.

### Database Schema
Three tables in `data/veille.db`:
- `favoris` - Saved articles with tags and thematique
- `historique_recherches` - Search/watch history
- `rapports` - Generated reports with content and optional Claude analysis

## Configuration

Requires `.env` file at project root:
```
NEWS_API_KEY=your_newsapi_key
ANTHROPIC_API_KEY=your_anthropic_key
```

Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "veille-system": {
      "command": "python",
      "args": ["path/to/src/veille_server.py"],
      "env": {"PYTHONPATH": "path/to/project"}
    }
  }
}
```

## Adding New Themes or RSS Feeds

Add themes to `THEMATIQUES` dict in `veille_server.py`:
```python
"Theme Name": {
    "description": "...",
    "keywords": ["keyword1", "keyword2"],
    "categorie": "IA"  # or "PRO"
}
```

Add RSS feeds to `RSS_FEEDS` dict by category.

Note: The dashboard imports `THEMATIQUES` from `veille_server.py` - single source of truth.

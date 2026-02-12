# Guide UV - Workflow Moderne

**Date**: February 11, 2026

---

## Setup complet (déjà fait ✅)

```bash
# 1. Créer pyproject.toml (fait)
# 2. Sync les dépendances
uv sync

# 3. Tout est prêt !
```

---

## Commandes principales

### Lancer du code

```bash
# Utiliser uv run (pas besoin d'activer .venv)
uv run python -m mcp_server.server

# Ou avec mcp dev
uv run mcp dev mcp_server/server.py

# Script Python
uv run python script.py
```

### Ajouter un package

```bash
# Ajouter à pyproject.toml puis sync
uv add package-name

# Ou manuellement:
# 1. Éditer pyproject.toml
# 2. uv sync
```

### Tests

```bash
# Installer les dépendances de dev
uv sync --extra dev

# Lancer les tests
uv run pytest tests/ -v
```

---

## Avantages de `uv sync`

| Aspect | `pip install -r requirements.txt` | `uv sync` |
|--------|----------------------------------|-----------|
| **Vitesse** | Lent | Ultra-rapide ⚡ |
| **Lock file** | ❌ Non | ✅ Oui (`uv.lock`) |
| **Reproductibilité** | ⚠️ Moyenne | ✅ Parfaite |
| **Gestion packages** | Manuel | Automatique |
| **Dev dependencies** | requirements-dev.txt | `[project.optional-dependencies]` |

---

## Workflow complet

### 1. Développement

```bash
# Ajouter une dépendance
uv add anthropic>=0.40.0

# Installer mode dev
uv sync --extra dev

# Lancer le code
uv run python -m mcp_server.server
```

### 2. Production

```bash
# Install production only (pas les dev deps)
uv sync --no-dev

# Lancer le serveur
uv run python -m mcp_server.server
```

### 3. Tests

```bash
# Install avec dev deps
uv sync --extra dev

# Run tests
uv run pytest -v

# Avec coverage
uv run pytest --cov=app --cov-report=html
```

---

## Configuration actuelle

Votre `pyproject.toml` contient:

```toml
[project]
name = "wealthpoint-analysis"
version = "1.2.0"
requires-python = ">=3.10"

dependencies = [
    "mcp>=1.0.0",
    "anthropic>=0.39.0",
    "pymupdf>=1.24.0",  # Claude Vision
    # ... autres packages
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

---

## Tester l'installation

```bash
# Test rapide
uv run python -c "
from app.parsers.pdf_router import PDFParserRouter
from app.llm import create_llm
print('✅ Claude Vision router ready!')
"

# Test avec fichier
uv run python -c "
from app.llm import create_llm
llm = create_llm()
print(f'✅ LLM Provider: {llm.__class__.__name__}')
"
```

---

## Troubleshooting

### Warning: VIRTUAL_ENV mismatch

C'est normal si vous avez un autre venv activé. `uv run` utilise automatiquement `.venv`.

Pour l'ignorer complètement:
```bash
deactivate  # désactiver l'autre venv
uv run python script.py
```

### Ajouter un package qui n'existe pas dans PyPI

```toml
[project]
dependencies = [
    "package-name @ git+https://github.com/user/repo.git",
]
```

---

## Next Steps

Tout est installé ! Vous pouvez maintenant:

1. **Tester le parser Claude Vision**:
   ```bash
   uv run python -c "
   from app.parsers.pdf_router import PDFParserRouter
   print('Router ready for multi-format PDFs!')
   "
   ```

2. **Lancer le serveur MCP**:
   ```bash
   uv run mcp dev mcp_server/server.py
   ```

3. **Configurer `.env`** (si pas déjà fait):
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   DATABASE_URL=sqlite:///./wealthpoint.db
   ```

---

**Installation réussie avec `uv sync` !** 🚀

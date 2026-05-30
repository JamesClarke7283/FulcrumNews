.PHONY: install css css-watch run dev ingest db-init test lint

CSS_IN  := src/fulcrumnews/static/css/input.css
CSS_OUT := src/fulcrumnews/static/css/output.css

install:        ## Install dependencies (incl. dev) into .venv
	uv sync --extra dev

css:            ## Build the minified Tailwind stylesheet
	uv run tailwindcss -i $(CSS_IN) -o $(CSS_OUT) --minify

css-watch:      ## Rebuild CSS on change (run alongside `make run`)
	uv run tailwindcss -i $(CSS_IN) -o $(CSS_OUT) --watch

db-init:        ## Create the SQLite schema and seed the default outlet roster
	uv run python -m fulcrumnews.tools.dbinit

ingest:         ## Run one full pipeline pass (fetch -> cluster -> bias -> summarize)
	uv run python -m fulcrumnews.graph.pipeline

run:            ## Serve the app (build CSS first if you haven't)
	uv run python -m fulcrumnews

dev:            ## Serve the app (assumes CSS already built; use css-watch in another shell)
	uv run python -m fulcrumnews

test:           ## Run the test suite
	uv run pytest -q

lint:           ## Lint with ruff
	uv run ruff check src tests

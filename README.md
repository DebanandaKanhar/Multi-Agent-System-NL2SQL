# Multi-Agent Cross-Database NL Analytics (Python)

Python-based multi-agent system that answers user questions across:
- PostgreSQL (customers)
- Cassandra (orders)
- MongoDB (support tickets)

It can combine data from multiple tables/databases, validate the result, and show visual outputs (line, pie, bar, histogram) in a Streamlit GUI.
It also includes intent confidence scoring, interpretation notes, and execution query logs for transparency.

## Architecture

Agents in sequence:
1. `QueryUnderstandingAgent` - interprets question into metric, dimensions, filters, chart hint.
2. `SchemaRoutingAgent` - maps intent to the right table(s) and database(s).
3. `QueryPlanningAgent` - builds join + aggregation plan.
4. `QueryExecutionAgent` - fetches data and executes joins/aggregations in pandas.
5. `ValidationAgent` - checks result quality.
6. `AnswerSynthesisAgent` - creates human-readable answer.
7. `VisualizationAgent` - creates Plotly chart.
8. Confidence and diagnostics are exposed in UI:
   - intent confidence score
   - interpretation notes
   - per-source query logs

Main entry point:
- `app.py` (Streamlit GUI)

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Open the local Streamlit URL printed in terminal.

## Local Sample Databases (PostgreSQL + Cassandra + MongoDB)

Use this to validate real cross-database behavior (not mock mode).

```bash
docker compose up -d
```

Update `.env`:

```bash
USE_MOCK_DATA=false
```

Create tables and seed data:

```bash
python -m scripts.setup_sample_data
```

Run verification script:

```bash
python -m scripts.verify_results
```

## Mock Mode vs Real Databases

By default, app runs with mock data:
- `USE_MOCK_DATA=true`

This lets you test immediately without setting up databases.

To use real databases:
1. Set `USE_MOCK_DATA=false` in `.env`.
2. Fill PostgreSQL/Cassandra/MongoDB connection settings.
3. Ensure tables exist with schemas matching `src/schema/catalog.yaml`.

## Optional LLM Intent Parser

The app includes an optional LLM-first parser for richer natural language interpretation.
If LLM parsing fails for any reason, it automatically falls back to deterministic parsing.
Provider defaults are auto-selected from `LLM_PROVIDER`, so `LLM_API_URL` and `LLM_MODEL` are optional.
Prompt templates and few-shot examples are stored in `src/prompts/intent_parser.yaml`.

Enable in `.env`:

```bash
ENABLE_LLM_PARSER=true
LLM_PROVIDER=openai
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=your_key_here
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=20
```

Groq setup:

```bash
ENABLE_LLM_PARSER=true
LLM_PROVIDER=groq
LLM_API_KEY=your_groq_key
LLM_TIMEOUT_SECONDS=20
```

Ollama setup:

```bash
ENABLE_LLM_PARSER=true
LLM_PROVIDER=ollama
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=30
```

## Example Questions

- `total sales by region monthly`
- `number of orders by product category`
- `average ticket resolution time by priority`
- `ticket count by region`
- `total sales by segment last 90 days`
- `ticket count by region`
- `total sales by region`

## Prompting Strategy

- **System prompt**: constrains output to strict JSON intent format.
- **Few-shot examples**: include representative mappings for sales/orders/tickets.
- **Reasoning control**: prompt requests internal reasoning but JSON-only output (no chain-of-thought output).
- **Fallback behavior**: if provider response is invalid, deterministic parser handles the query.

## Project Structure

```
app.py
src/
  agents/
  config.py
  data/
  models.py
  schema/catalog.yaml
  utils/
```

## Notes

- This is a robust baseline design for multi-database NL analytics.
- You can upgrade the `QueryUnderstandingAgent` with an LLM parser later for richer intent extraction.
- Current implementation uses deterministic routing/planning logic and pandas-based execution for transparency.
- Streamlit dashboard renders multiple visuals per query (primary chart + supporting charts).

# Development Exercise Steps

This file captures the exact process followed to build this multi-agent, multi-database NL analytics exercise.

## 1) Goal Definition

- Build a Python-only system where users ask natural-language questions.
- Support data from three databases:
  - PostgreSQL (`customers`)
  - Cassandra (`orders`)
  - MongoDB (`support_tickets`)
- Handle cross-table and cross-database combinations.
- Validate results and show visual output (line, bar, pie, distribution).
- Provide a Python GUI for interaction.

## 2) Project Scaffolding

- Created base folders:
  - `src/agents`
  - `src/data`
  - `src/schema`
  - `src/utils`
- Added dependency file:
  - `requirements.txt`
- Added config and models:
  - `src/config.py`
  - `src/models.py`

## 3) Data Contract and Schema Mapping

- Added table catalog in `src/schema/catalog.yaml`:
  - PostgreSQL: `customers`
  - Cassandra: `orders`
  - MongoDB: `support_tickets`
- Added utility loader:
  - `src/utils/catalog.py`

## 4) Multi-Agent Architecture Implementation

Implemented specialized agents:

- `QueryUnderstandingAgent` (`src/agents/understanding_agent.py`)
  - Parses user question into structured intent.
- `SchemaRoutingAgent` (`src/agents/routing_agent.py`)
  - Chooses source database/table(s).
- `QueryPlanningAgent` (`src/agents/planning_agent.py`)
  - Creates join + aggregation plan.
- `QueryExecutionAgent` (`src/agents/execution_agent.py`)
  - Fetches data and executes joins/aggregation in pandas.
- `ValidationAgent` (`src/agents/validation_agent.py`)
  - Basic correctness checks.
- `AnswerSynthesisAgent` (`src/agents/answer_agent.py`)
  - Converts output to human-friendly text.
- `VisualizationAgent` (`src/agents/visualization_agent.py`)
  - Builds primary + supporting charts.
- `MultiAgentOrchestrator` (`src/agents/orchestrator.py`)
  - Runs all agents in sequence and returns final payload.

## 5) Data Access Layer

- Added adapters in `src/data/adapters.py`:
  - PostgreSQL via `psycopg`
  - Cassandra via `cassandra-driver`
  - MongoDB via `pymongo`
- Added unified gateway:
  - `src/data/gateway.py`
- Added mock dataset generator for zero-setup testing:
  - `src/utils/mock_data.py`

## 6) GUI and User Interaction

- Built Streamlit app in `app.py`:
  - question input
  - text answer
  - validation messages
  - result table
  - chart rendering
  - agent trace
  - query logs
  - confidence + interpretation notes

## 7) LLM Intent Parser Upgrade

- Added optional LLM parser with deterministic fallback.
- Added provider support:
  - OpenAI-compatible
  - Groq
  - Ollama
- Added provider-aware defaults in config:
  - `LLM_PROVIDER`, `LLM_API_URL`, `LLM_MODEL`, etc.
- Added fallback diagnostics to notes when LLM parsing fails.

## 8) Prompt Engineering Assets

- Added prompt bundle:
  - `src/prompts/intent_parser.yaml`
- Included:
  - system prompt
  - few-shot examples
  - internal reasoning checklist
- Added prompt loader:
  - `src/utils/prompt_loader.py`
- Wired understanding agent to build messages from this prompt bundle.

## 9) Real Database Exercise Setup

- Added `docker-compose.yml` for local DB services.
- Added seed script:
  - `scripts/setup_sample_data.py`
  - Creates DB/keyspace/tables and inserts sample rows.
- Added verification script:
  - `scripts/verify_results.py`
  - Runs representative questions and checks output is non-empty.

## 10) Environment Setup Pattern

- `.env.example` used as template.
- `.env` configured for local use (Ollama default enabled).
- Typical run pattern:
  1. Create Python virtual environment.
  2. Install dependencies.
  3. Start DB services.
  4. Seed sample data.
  5. Verify via script.
  6. Start Streamlit app.

## 11) Verification Steps Executed

The implementation was validated using:

- Python compile checks for all modules/scripts.
- Lint diagnostics checks after edits.
- Data seeding script run.
- Verification script run with real DB mode:
  - `USE_MOCK_DATA=false`
  - `ENABLE_LLM_PARSER=false`
- Successful sample question outputs confirmed.

## 12) Commands Used in the Exercise

Use these as your repeatable exercise workflow:

```bash
# 1) Create and activate environment
python3.12 -m venv .venv312
source .venv312/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Start sample services (as needed)
docker compose up -d

# 4) Seed data
python -m scripts.setup_sample_data

# 5) Verify outputs
USE_MOCK_DATA=false ENABLE_LLM_PARSER=false python -m scripts.verify_results

# 6) Run app
streamlit run app.py
```

## 13) Recommended Practice Extensions

- Add additional tables and foreign-key-style join paths.
- Add stronger validation checks (null rate, anomaly checks, row-count expectations).
- Add automated tests for routing and planning logic.
- Add provider-level retries and response schema enforcement for LLM calls.
- Add a reusable Makefile for one-command setup/verify/run.


from __future__ import annotations

import time
import streamlit as st

from src.agents.orchestrator import MultiAgentOrchestrator
from src.config import load_settings


st.set_page_config(page_title="Multi-Agent NL2Data", layout="wide")

st.title("Multi-Agent Cross-Database Analytics")
st.caption("Ask questions across PostgreSQL, Cassandra, and MongoDB from one interface.")

settings = load_settings()
orchestrator = MultiAgentOrchestrator(settings)


def render_agent_interactions(output) -> None:
    intent = output.result.intent
    plan = output.result.plan
    result_df = output.result.result_df
    metric_col = next(
        (c for c in ["total_sales", "order_count", "ticket_count", "avg_resolution_time"] if c in result_df.columns),
        None,
    )

    st.subheader("How Agents Interact")
    st.markdown(
        "User Question -> UnderstandingAgent -> RoutingAgent -> PlanningAgent -> "
        "ExecutionAgent -> ValidationAgent -> AnswerAgent -> VisualizationAgent"
    )

    interactions = [
        {
            "title": "1) UnderstandingAgent -> RoutingAgent",
            "summary": "Intent extracted from user question.",
            "payload": {
                "raw_question": intent.raw_question,
                "metric": intent.metric,
                "dimensions": intent.dimensions,
                "filters": intent.filters,
                "chart_hint": intent.chart_hint,
                "time_granularity": intent.time_granularity,
                "confidence": intent.confidence,
            },
        },
        {
            "title": "2) RoutingAgent -> PlanningAgent",
            "summary": "Selected source tables across databases.",
            "payload": {
                "requests": [
                    {
                        "source": req.source,
                        "table": req.table,
                        "required_columns": req.required_columns,
                    }
                    for req in plan.requests
                ]
            },
        },
        {
            "title": "3) PlanningAgent -> ExecutionAgent",
            "summary": "Join and aggregation plan prepared.",
            "payload": {
                "joins": plan.joins,
                "aggregations": plan.aggregations,
            },
        },
        {
            "title": "4) ExecutionAgent -> ValidationAgent",
            "summary": "Executed plan and produced result dataframe.",
            "payload": {
                "row_count": int(len(result_df)),
                "columns": list(result_df.columns),
                "query_logs": output.result.query_logs,
            },
        },
        {
            "title": "5) ValidationAgent -> AnswerAgent",
            "summary": "Validation outcome attached to result.",
            "payload": {
                "is_valid": output.result.validation.is_valid,
                "messages": output.result.validation.messages,
            },
        },
        {
            "title": "6) AnswerAgent -> VisualizationAgent",
            "summary": "Answer text and metric context shared for charting.",
            "payload": {
                "answer_preview": output.result.answer_text[:220] + ("..." if len(output.result.answer_text) > 220 else ""),
                "metric_column": metric_col,
                "available_charts": list(output.dashboard.keys()),
            },
        },
    ]

    for item in interactions:
        with st.expander(item["title"], expanded=False):
            st.write(item["summary"])
            st.json(item["payload"])


def _status_badge(status: str) -> str:
    if status == "completed":
        return "Done"
    if status == "active":
        return "Running"
    return "Pending"


def _render_level(level_title: str, steps: list[dict], active_idx: int, start_idx: int) -> str:
    cards: list[str] = []
    for offset, step in enumerate(steps):
        idx = start_idx + offset
        if idx < active_idx:
            status = "completed"
        elif idx == active_idx:
            status = "active"
        else:
            status = "pending"

        cards.append(
            f"""
            <div class="agent-card {status}">
              <div class="agent-icon">{step["icon"]}</div>
              <div class="agent-name">{step["name"]}</div>
              <div class="agent-meta">Level {step["level"]}</div>
              <div class="agent-status">{_status_badge(status)}</div>
            </div>
            """
        )
        if offset < len(steps) - 1:
            cards.append('<div class="agent-arrow">→</div>')
    return f"""
    <div class="level-title">{level_title}</div>
    <div class="agent-row">{''.join(cards)}</div>
    """


def render_agent_stepper(output) -> None:
    st.subheader("Agent Workflow")
    st.caption("Each stage completes, then transitions to the next stage.")
    st.markdown(
        """
        <style>
        .level-title { font-weight: 600; margin: 0.5rem 0 0.4rem 0; color: #34495e; }
        .agent-row { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
        .agent-card {
            min-width: 145px; border-radius: 12px; padding: 10px 12px;
            border: 1px solid #e1e5ea; background: #f7f9fc;
            box-shadow: 0 1px 2px rgba(20,20,20,0.06);
        }
        .agent-card .agent-icon { font-size: 22px; line-height: 1.1; }
        .agent-card .agent-name { font-size: 13px; font-weight: 600; margin-top: 4px; }
        .agent-card .agent-meta { font-size: 11px; color: #6b7280; margin-top: 2px; }
        .agent-card .agent-status { font-size: 11px; margin-top: 6px; font-weight: 600; }
        .agent-card.pending .agent-status { color: #9ca3af; }
        .agent-card.active {
            border-color: #2563eb; background: #eff6ff; transform: translateY(-1px);
            box-shadow: 0 3px 10px rgba(37,99,235,0.18);
        }
        .agent-card.active .agent-status { color: #1d4ed8; }
        .agent-card.completed { border-color: #16a34a; background: #f0fdf4; }
        .agent-card.completed .agent-status { color: #15803d; }
        .agent-arrow { font-size: 20px; color: #94a3b8; padding: 0 2px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        {"icon": "❓", "name": "User Question", "level": 0},
        {"icon": "🧠", "name": "Understanding", "level": 1},
        {"icon": "🧭", "name": "Routing", "level": 1},
        {"icon": "🗺️", "name": "Planning", "level": 1},
        {"icon": "⚙️", "name": "Execution", "level": 2},
        {"icon": "✅", "name": "Validation", "level": 2},
        {"icon": "💬", "name": "Answer", "level": 3},
        {"icon": "📊", "name": "Visualization", "level": 3},
    ]

    top = steps[:4]
    bottom = steps[4:]
    placeholder = st.empty()

    for active_idx in range(len(steps)):
        top_html = _render_level("Level 0-1 (Understanding & Planning)", top, active_idx, 0)
        bottom_html = _render_level("Level 2-3 (Execution to Presentation)", bottom, active_idx, len(top))
        placeholder.markdown(top_html + bottom_html, unsafe_allow_html=True)
        time.sleep(0.12)

    rows = len(output.result.result_df)
    validation = "Passed" if output.result.validation.is_valid else "Failed"
    charts = len(output.dashboard)
    st.info(f"Workflow completed: rows={rows}, validation={validation}, charts={charts}")


with st.sidebar:
    st.subheader("Runtime")
    st.write(f"Mock data mode: `{settings.use_mock_data}`")
    st.write(f"Max rows/table scan: `{settings.max_rows_per_table_scan}`")
    st.write(f"LLM parser enabled: `{settings.llm.enabled}`")
    st.write(f"LLM provider: `{settings.llm.provider}`")
    st.write(f"LLM model: `{settings.llm.model}`")
    st.markdown(
        "Example queries:\n"
        "- total sales by region monthly\n"
        "- number of orders by product category\n"
        "- average ticket resolution time by priority\n"
        "- ticket count by region"
    )

question = st.text_input(
    "Ask a business question",
    value="total sales by region monthly",
    help="The system routes your query to one or more data sources and validates the result.",
)

if st.button("Run Query", type="primary"):
    with st.spinner("Running multi-agent workflow..."):
        output = orchestrator.run(question)

    render_agent_stepper(output)

    render_agent_interactions(output)

    st.subheader("Answer")
    st.write(output.result.answer_text)
    st.progress(output.result.intent.confidence, text=f"Intent confidence: {output.result.intent.confidence:.2f}")

    if output.result.intent.interpretation_notes:
        with st.expander("Interpretation Notes"):
            for note in output.result.intent.interpretation_notes:
                st.write(f"- {note}")

    st.subheader("Validation")
    for msg in output.result.validation.messages:
        st.write(f"- {msg}")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Result Table")
        st.dataframe(output.result.result_df, use_container_width=True)
    with right:
        st.subheader("Primary Visualization")
        if output.figure is not None:
            st.plotly_chart(output.figure, use_container_width=True)
        else:
            st.info("No chart suggestion for this result.")

    st.subheader("Dashboard Visuals")
    dashboard = {k: v for k, v in output.dashboard.items() if k != "Primary"}
    if dashboard:
        cols = st.columns(2)
        for idx, (title, fig) in enumerate(dashboard.items()):
            with cols[idx % 2]:
                st.markdown(f"**{title}**")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No additional visuals for this query.")

    with st.expander("Execution Query Logs"):
        for log in output.result.query_logs:
            st.code(log, language="text")

    st.subheader("Agent Trace")
    for step in output.result.trace:
        st.code(step, language="text")

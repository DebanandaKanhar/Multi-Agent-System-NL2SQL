from __future__ import annotations

from dataclasses import dataclass
import plotly.graph_objects as go

from src.agents.answer_agent import AnswerSynthesisAgent
from src.agents.execution_agent import QueryExecutionAgent
from src.agents.planning_agent import QueryPlanningAgent
from src.agents.routing_agent import SchemaRoutingAgent
from src.agents.understanding_agent import QueryUnderstandingAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.visualization_agent import VisualizationAgent
from src.config import Settings
from src.data.gateway import HybridDataGateway
from src.models import AgentResult


@dataclass
class OrchestratorOutput:
    result: AgentResult
    figure: go.Figure | None
    dashboard: dict[str, go.Figure]


class MultiAgentOrchestrator:
    def __init__(self, settings: Settings):
        gateway = HybridDataGateway(settings)
        self.understanding = QueryUnderstandingAgent(settings)
        self.routing = SchemaRoutingAgent()
        self.planning = QueryPlanningAgent()
        self.execution = QueryExecutionAgent(gateway)
        self.validation = ValidationAgent()
        self.answering = AnswerSynthesisAgent()
        self.viz = VisualizationAgent()

    def run(self, question: str) -> OrchestratorOutput:
        trace: list[str] = []

        intent = self.understanding.analyze(question)
        trace.append(f"UnderstandingAgent -> metric={intent.metric}, dims={intent.dimensions}")

        requests = self.routing.route(intent)
        trace.append(
            "RoutingAgent -> "
            + ", ".join([f"{r.source}.{r.table}" for r in requests])
        )

        plan = self.planning.plan(intent, requests)
        trace.append(
            f"PlanningAgent -> joins={len(plan.joins)}, aggs={len(plan.aggregations)}"
        )

        result_df, query_logs = self.execution.execute(intent, plan)
        trace.append(f"ExecutionAgent -> rows={len(result_df)}")

        validation = self.validation.validate(intent, result_df)
        trace.append(
            f"ValidationAgent -> is_valid={validation.is_valid} ({'; '.join(validation.messages)})"
        )

        answer = self.answering.compose(intent, result_df, validation)
        trace.append("AnswerAgent -> synthesized text answer")

        dashboard = self.viz.build_dashboard(intent, result_df)
        fig = dashboard.get("Primary")
        trace.append("VisualizationAgent -> chart generated" if fig else "VisualizationAgent -> no chart")

        agent_result = AgentResult(
            intent=intent,
            plan=plan,
            answer_text=answer,
            result_df=result_df,
            validation=validation,
            query_logs=query_logs,
            trace=trace,
        )
        return OrchestratorOutput(result=agent_result, figure=fig, dashboard=dashboard)

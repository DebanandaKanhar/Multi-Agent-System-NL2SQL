from __future__ import annotations

from src.agents.orchestrator import MultiAgentOrchestrator
from src.config import load_settings


def main() -> None:
    settings = load_settings()
    orchestrator = MultiAgentOrchestrator(settings)

    questions = [
        "total sales by region monthly",
        "number of orders by product category",
        "average ticket resolution time by priority",
        "ticket count by region",
    ]

    for idx, question in enumerate(questions, start=1):
        output = orchestrator.run(question)
        print(f"\n[{idx}] {question}")
        print(f"Answer: {output.result.answer_text}")
        print(f"Rows: {len(output.result.result_df)}")
        print(f"Valid: {output.result.validation.is_valid}")
        print(f"Trace: {output.result.trace[-1] if output.result.trace else 'n/a'}")

        if output.result.result_df.empty:
            raise RuntimeError(f"Verification failed for question: {question}")

    print("\nVerification passed for all sample questions.")


if __name__ == "__main__":
    main()

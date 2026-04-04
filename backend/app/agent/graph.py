"""
LangGraph interview graph.
Pure LangGraph — no LangChain dependency.

Flow:
    START → greet → ask_question → evaluate_answer
                        ↑                 ↓ (should_continue)
                        └─────────────────┘
                                         ↓ (when max_questions reached)
                                      summarize → END
"""
from langgraph.graph import StateGraph, START, END

from app.agent.state import InterviewState
from app.agent.nodes import (
    greet_node,
    ask_question_node,
    evaluate_answer_node,
    summarize_node,
    should_continue,
)


def build_interview_graph():
    graph = StateGraph(InterviewState)

    # Register nodes
    graph.add_node("greet", greet_node)
    graph.add_node("ask_question", ask_question_node)
    graph.add_node("evaluate_answer", evaluate_answer_node)
    graph.add_node("summarize", summarize_node)

    # Edges
    graph.add_edge(START, "greet")
    graph.add_edge("greet", "ask_question")

    # ask_question → evaluate_answer
    # (the graph is logically interrupted here in practice — the Kafka consumer
    # injects the user's answer into state before calling evaluate_answer)
    graph.add_edge("ask_question", "evaluate_answer")

    # Conditional: loop back or finish
    graph.add_conditional_edges(
        "evaluate_answer",
        should_continue,
        {
            "ask_question": "ask_question",
            "summarize": "summarize",
        },
    )
    graph.add_edge("summarize", END)

    return graph.compile()


# Singleton — imported by the Kafka consumer
interview_graph = build_interview_graph()

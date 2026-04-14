from src.data.schemas import RouteDecision


def route_message(message_text: str) -> RouteDecision:
    text = message_text.lower()

    handoff_keywords = [
        "complaint",
        "report",
        "agent",
        "help me",
        "speak to someone",
        "fraud",
        "spam",
    ]

    if any(keyword in text for keyword in handoff_keywords):
        return RouteDecision(
            route="handoff",
            confidence=0.7,
            reason="Matched simple handoff keywords.",
        )

    return RouteDecision(
        route="faq",
        confidence=0.6,
        reason="Defaulting to retrieval-based FAQ response.",
    )
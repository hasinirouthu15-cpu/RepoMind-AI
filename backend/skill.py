
def analyze_question(question: str) -> str:
    """
    Understand the user's question and prepare it
    for the AI model.
    """
    question = question.strip()

    if not question:
        return "Please enter a question."

    return (
        "You are RepoMind AI, an AI-powered codebase "
        "intelligence assistant. Help explain code, "
        "find bugs, and suggest improvements.\n\n"
        f"User question: {question}"
    )

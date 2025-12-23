from typing import TypedDict, Optional

class PassedState(TypedDict):
    question: str
    schema: dict
    query: str
    result: Optional[list]
    error: Optional[str]
    attempts: int
    final_answer: Optional[str]
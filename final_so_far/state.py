from typing import TypedDict, Optional

class PassedState(TypedDict):
    question: str
    tables: Optional[list]
    schema: str
    query: str
    result: Optional[list]
    error: Optional[str]
    attempts: int
    final_answer: Optional[str]
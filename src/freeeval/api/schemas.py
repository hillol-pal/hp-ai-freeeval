from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmptyStr = Annotated[str, Field(min_length=1)]
UseCase = Literal["prompt", "rag", "agent"]
StepKind = Literal["model", "retrieve", "tool", "observe"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Score(APIModel):
    name: Literal["exact_match"]
    value: bool
    passed: bool


class CaseResult(APIModel):
    case_id: str
    scores: list[Score]


class Summary(APIModel):
    case_count: int
    scored_count: int
    passed_count: int


class RunRecord(APIModel):
    run_id: str
    use_case: UseCase
    results: list[CaseResult]
    summary: Summary


class UniqueCases(APIModel):
    @model_validator(mode="after")
    def reject_duplicate_ids(self) -> "UniqueCases":
        ids = [case.id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("case ids must be unique")
        return self


class Context(APIModel):
    id: NonEmptyStr
    text: str


class RagCase(APIModel):
    id: NonEmptyStr
    question: str
    answer: str
    contexts: list[Context]
    expected_answer: str | None = None
    relevant_context_ids: list[str] | None = None


class RagEvaluationRequest(UniqueCases):
    cases: list[RagCase] = Field(min_length=1)


class AgentStep(APIModel):
    kind: StepKind
    name: NonEmptyStr
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    error: str | None = None


class AgentCase(APIModel):
    id: NonEmptyStr
    task: str
    output: str
    steps: list[AgentStep]
    expected_output: str | None = None


class AgentEvaluationRequest(UniqueCases):
    cases: list[AgentCase] = Field(min_length=1)

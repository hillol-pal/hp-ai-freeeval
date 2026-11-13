from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmptyStr = Annotated[str, Field(min_length=1)]
UseCase = Literal["prompt", "code", "rag", "agent"]
StepKind = Literal["model", "retrieve", "tool", "observe"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Score(APIModel):
    name: NonEmptyStr
    value: bool | float | None
    passed: bool | None
    reason: str | None = None


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


PromptMetricName = Literal["answer_relevancy", "conciseness", "specificity"]
PromptVerdict = Literal["pass", "fail"]


class PromptMetricSpec(APIModel):
    name: PromptMetricName
    threshold: float = Field(ge=0, le=1)


class PromptEvaluationRequest(APIModel):
    prompt: NonEmptyStr = Field(description="Input prompt given to the model.")
    answer: NonEmptyStr = Field(description="Model answer to score against the prompt.")
    metrics: list[PromptMetricSpec] = Field(
        min_length=1,
        description="Metrics to run. Each metric has its own threshold from 0 to 1.",
    )

    @model_validator(mode="after")
    def reject_duplicate_metrics(self) -> "PromptEvaluationRequest":
        names = [metric.name for metric in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("metrics must be unique")
        return self


class PromptMetricResult(APIModel):
    name: PromptMetricName
    result: PromptVerdict
    reasoning: str


class PromptEvaluationResponse(APIModel):
    run_id: NonEmptyStr
    metrics: list[PromptMetricResult]


class APIError(APIModel):
    error_code: str
    reason_code: str
    message: str


class CodeCase(APIModel):
    id: NonEmptyStr
    code: str
    output: str
    expected: str | None = None


class CodeEvaluationRequest(UniqueCases):
    cases: list[CodeCase] = Field(min_length=1)


RagMetricName = Literal["faithfulness", "answer_relevancy"]


class RagMetricSpec(APIModel):
    name: RagMetricName
    threshold: float = Field(ge=0, le=1)


class RagEvaluationRequest(APIModel):
    query: NonEmptyStr = Field(description="Question or query sent to the RAG system.")
    actual_response: NonEmptyStr = Field(description="Answer produced for the query.")
    retrieved_contexts: list[NonEmptyStr] = Field(
        description="Context passages retrieved for the query. The list may be empty.",
    )
    metrics: list[RagMetricSpec] = Field(
        min_length=1,
        description="Metrics to run. Each metric has its own threshold from 0 to 1.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Caller metadata. It is accepted and is not scored.",
    )

    @model_validator(mode="after")
    def reject_duplicate_metrics(self) -> "RagEvaluationRequest":
        names = [metric.name for metric in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("metrics must be unique")
        return self


class RagMetricResult(APIModel):
    name: RagMetricName
    result: PromptVerdict
    reasoning: str


class RagEvaluationResponse(APIModel):
    run_id: NonEmptyStr
    metrics: list[RagMetricResult]


AgentMetricName = Literal["task_success_rate", "tool_call_accuracy"]


class AgentMetricSpec(APIModel):
    name: AgentMetricName
    threshold: float = Field(ge=0, le=1)


class TraceEvent(APIModel):
    kind: StepKind
    name: NonEmptyStr
    arguments: dict[str, Any] | None = None
    expected_name: str | None = None
    expected_arguments: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    error: str | None = None


class AgentEvaluationRequest(APIModel):
    input: NonEmptyStr = Field(description="Task given to the agent.")
    actual_output: NonEmptyStr = Field(description="Final output the agent produced.")
    execution_trace: list[TraceEvent] = Field(
        description="Steps the agent recorded. The list may be empty.",
    )
    metrics: list[AgentMetricSpec] = Field(
        min_length=1,
        description="Metrics to run. Each metric has its own threshold from 0 to 1.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Caller metadata. It is accepted and is not scored.",
    )

    @model_validator(mode="after")
    def reject_duplicate_metrics(self) -> "AgentEvaluationRequest":
        names = [metric.name for metric in self.metrics]
        if len(names) != len(set(names)):
            raise ValueError("metrics must be unique")
        return self


class AgentMetricResult(APIModel):
    name: AgentMetricName
    result: PromptVerdict
    reasoning: str


class AgentEvaluationResponse(APIModel):
    run_id: NonEmptyStr
    metrics: list[AgentMetricResult]

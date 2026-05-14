from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class WorkflowStep(BaseModel):
    id: str
    label: str
    type: str  # process, decision, start, end, input, output
    description: str = ""
    is_decision_node: bool = False
    human_judgment_required: str | None = None
    next: list[str] = []


class APIEndpoint(BaseModel):
    method: str  # GET, POST, PUT, DELETE
    path: str
    description: str = ""
    request_body: dict[str, Any] = {}
    response_body: dict[str, Any] = {}


class APISpec(BaseModel):
    endpoints: list[APIEndpoint] = []


class DecisionNode(BaseModel):
    step_id: str
    question: str
    tradeoffs: list[str] = []
    human_accountability: str = ""


class WorkflowMetadata(BaseModel):
    generated_by: str = ""
    human_authorizer: str = ""


class WorkflowOutput(BaseModel):
    workflow: Workflow
    mermaid_code: str
    api_spec: APISpec
    decision_nodes: list[DecisionNode]
    metadata: WorkflowMetadata


class Workflow(BaseModel):
    title: str
    description: str = ""
    steps: list[WorkflowStep] = []


class GenerateRequest(BaseModel):
    prompt: str

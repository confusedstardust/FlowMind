import json
import re
from models import WorkflowOutput


def parse_and_validate(raw_json: str) -> WorkflowOutput:
    """解析 AI 返回的 JSON 并验证。"""
    cleaned = _clean_json(raw_json)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回了无效的 JSON: {e}")

    result = WorkflowOutput(**data)
    _validate_mermaid(result.mermaid_code)
    _validate_decision_nodes(result)
    return result


def _clean_json(raw: str) -> str:
    """移除 markdown 代码块包裹和多余空白。"""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw


def _validate_mermaid(code: str) -> None:
    """检查 Mermaid 代码是否以有效关键字开头。"""
    if not code:
        raise ValueError("Mermaid 代码不能为空")
    first_line = code.strip().split("\n")[0].strip().lower()
    valid_starts = ("graph", "flowchart", "sequencediagram", "classdiagram",
                    "statediagram", "erDiagram", "gantt", "pie", "gitGraph")
    if not any(first_line.startswith(s.lower().replace(" ", "")) for s in valid_starts):
        if not any(first_line.startswith(s) for s in valid_starts):
            raise ValueError(f"Mermaid 代码格式无效，首行: {first_line}")


def _validate_decision_nodes(result: WorkflowOutput) -> None:
    """确保 is_decision_node=True 的步骤在 decision_nodes 中有对应条目。"""
    decision_step_ids = {
        s.id for s in result.workflow.steps if s.is_decision_node
    }
    declared_ids = {d.step_id for d in result.decision_nodes}
    missing = decision_step_ids - declared_ids
    if missing:
        raise ValueError(f"决策步骤 {missing} 在 decision_nodes 中缺少说明")
    extra = declared_ids - decision_step_ids
    if extra:
        raise ValueError(f"decision_nodes 中存在不匹配的步骤id: {extra}")

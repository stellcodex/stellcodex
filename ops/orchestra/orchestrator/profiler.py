from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Tuple

from scorer import TASK_SCORE_KEYS, score_output

CallModel = Callable[[str, List[Dict[str, str]], int], Awaitable[Tuple[str, Dict[str, Any]]]]

MODEL_TASKS: Dict[str, List[str]] = {
    "gemini_conductor": ["plan", "analysis"],
    "codex_executor": ["code"],
    "claude_reviewer": ["review"],
    "abacus_analyst": ["analysis"],
    "local_fast": ["ops_check", "doc"],
    "local_reason": ["analysis", "review"],
}

MICRO_TASKS_MINI: Dict[str, List[str]] = {
    "plan": [
        "Return a 3-step execution plan with acceptance criteria and rollback.",
        "Create a concise 4-step plan to add one API endpoint safely.",
    ],
    "code": [
        "Output a minimal unified diff that adds one env var and rollback notes.",
        "Provide a tiny patch and smoke test command for a FastAPI app.",
    ],
    "review": [
        "Review this patch summary and return PASS or FAIL, findings, and tests.",
        "Give a concise risk review with concrete test commands.",
    ],
    "analysis": [
        "Analyze deployment risks as bullets with actionable checks.",
        "Provide assumptions, risks, and next checks for a backend rollout.",
    ],
    "ops_check": [
        "Write an operations checklist for a dockerized service deployment.",
    ],
    "doc": [
        "Write a brief operator note with run, verify, and rollback steps.",
    ],
}

MICRO_TASKS_FULL: Dict[str, List[str]] = {
    task_type: prompts + [
        f"Produce another example for {task_type} with strict structure and rollback details."
    ]
    for task_type, prompts in MICRO_TASKS_MINI.items()
}


def _avg(values: List[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


async def run_profile(
    mode: str,
    call_model: CallModel,
    profiles: Dict[str, Any],
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    prompts_by_type = MICRO_TASKS_FULL if mode == "full" else MICRO_TASKS_MINI

    model_profiles = profiles.setdefault("models", {})
    attempted = 0
    succeeded = 0

    for model, task_types in MODEL_TASKS.items():
        model_state = model_profiles.setdefault(model, {})
        per_type_scores: Dict[str, List[float]] = {}

        for task_type in task_types:
            prompts = prompts_by_type.get(task_type, [])
            for prompt in prompts:
                attempted += 1
                messages = [
                    {"role": "system", "content": "You are a strict benchmark assistant."},
                    {"role": "user", "content": prompt},
                ]
                try:
                    output, _meta = await call_model(model, messages, timeout_seconds)
                except Exception:
                    continue
                succeeded += 1
                per_type_scores.setdefault(task_type, []).append(score_output(task_type, output))

        for task_type, scores in per_type_scores.items():
            if not scores:
                continue
            score_key = TASK_SCORE_KEYS.get(task_type, "analysis_score")
            model_state[score_key] = _avg(scores)

        model_state["last_profile_mode"] = mode
        model_state["last_profile_attempted"] = attempted
        model_state["last_profile_succeeded"] = succeeded

    profiles["last_profile_attempted"] = attempted
    profiles["last_profile_succeeded"] = succeeded
    return profiles

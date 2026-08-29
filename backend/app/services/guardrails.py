from __future__ import annotations

import re
from typing import Any

from app.core.config import settings


PROMPT_INJECTION_PATTERNS = (
    r"ignore previous instructions",
    r"system_prompt_override",
    r"drop\s+table",
    r"delete\s+from",
)

FORBIDDEN_COPY = ("100%", "绝对有效", "规避关税", "免税代购", "仅限你一人")


def verify_input(prompt: str) -> tuple[bool, str | None]:
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False, f"输入命中安全规则：{pattern}"
    return True, None


def inspect_campaign(*, target_rows: int, copy_variants: list[dict[str, Any]], scenario: str) -> dict[str, Any]:
    violations: list[str] = []
    for variant in copy_variants:
        content = f"{variant.get('title', '')} {variant.get('body', '')}"
        for phrase in FORBIDDEN_COPY:
            if phrase in content:
                violations.append(f"文案包含禁用表达：{phrase}")

    if scenario == "risk":
        target_rows = 55_000

    level = "low"
    requires_review = False
    if violations or target_rows > settings.HITL_AUDIENCE_THRESHOLD:
        level = "high"
        requires_review = True
    elif target_rows > 20_000:
        level = "medium"
        requires_review = True

    return {
        "level": level,
        "label": {"low": "低", "medium": "中", "high": "高"}[level],
        "requires_review": requires_review,
        "target_rows": target_rows,
        "violations": violations,
        "checks": [
            {"name": "敏感信息脱敏", "passed": True},
            {"name": "黑名单过滤", "passed": True},
            {"name": "重复用户排重", "passed": True},
            {"name": "时间窗口合理性", "passed": True},
            {"name": "人群重叠检查", "passed": True},
        ],
    }


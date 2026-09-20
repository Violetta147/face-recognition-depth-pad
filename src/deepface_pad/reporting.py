from __future__ import annotations


def select_depth_cases(rows: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    """Prefer mistakes, then borderline correct cases, without duplication."""
    if count <= 0:
        raise ValueError("count must be positive")
    errors = sorted(
        (row for row in rows if not bool(row["correct"])),
        key=lambda row: abs(float(row["score"]) - float(row["threshold"])),
        reverse=True,
    )
    correct = sorted(
        (row for row in rows if bool(row["correct"])),
        key=lambda row: abs(float(row["score"]) - float(row["threshold"])),
    )
    error_quota = min(len(errors), max(1, count // 2))
    selected = errors[:error_quota]
    selected.extend(correct[: count - len(selected)])
    if len(selected) < count:
        selected.extend(errors[error_quota : error_quota + count - len(selected)])
    return selected[:count]

def estimate_max_ai_calls(
    total_items: int,
    max_attempts: int,
) -> int:
    if total_items < 0:
        raise ValueError(
            "Total items cannot be negative."
        )

    if max_attempts < 1:
        raise ValueError(
            "Maximum attempts must be at least 1."
        )

    return total_items * max_attempts


def enforce_ai_call_budget(
    total_items: int,
    max_attempts: int,
    max_calls: int,
) -> int:
    estimated_calls = estimate_max_ai_calls(
        total_items=total_items,
        max_attempts=max_attempts,
    )

    if estimated_calls > max_calls:
        raise ValueError(
            "AI call budget exceeded. "
            f"Estimated maximum calls: "
            f"{estimated_calls}. "
            f"Allowed: {max_calls}."
        )

    return estimated_calls

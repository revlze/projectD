from project_d.evaluation.plots import pareto_front


def test_pareto_front_minimizes_tokens_and_maximizes_utility() -> None:
    points = {
        "cheap": (10, 0.6),
        "cheap_tie": (10, 0.6),
        "same_cost_worse": (10, 0.5),
        "same_utility_expensive": (12, 0.6),
        "quality": (20, 0.9),
        "strictly_dominated": (24, 0.8),
    }
    assert pareto_front(points) == {"cheap", "cheap_tie", "quality"}

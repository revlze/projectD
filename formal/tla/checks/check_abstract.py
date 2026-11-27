"""Independent finite execution check (not TLC or a parser for TLA+)."""
from collections import deque
from itertools import product

# Each job can be idle, pending, running, or completed, with one option fixed at acceptance.
JOBS = ("qa", "report", "regression", "ablation")
COST = ((7, 4), (2,), (6,), (1,))
REQUIRES = (None, 0, None, 2)
PAIRS = frozenset((j, o) for j, opts in enumerate(COST) for o in range(len(opts)))
PLANS = [frozenset((j, o) for j, o in enumerate(opts) if o >= 0)
         for opts in product(*(range(-1, len(c)) for c in COST))]


def total(pairs):
    return sum(COST[j][o] for j, o in pairs)


def explore(atomic, guard, deferred, budget, plan):
    # plan=None represents absence of agreement, not an explicitly empty agreement.
    initial = ((0, -1),) * 4, None, frozenset()
    seen = {initial}
    queue = deque([initial])
    violation = active_violation = release_seen = False
    transitions = 0
    while queue:
        states, release, guarded = queue.popleft()
        accepted = frozenset((j, o) for j, (stage, o) in enumerate(states) if stage)
        pending = frozenset((j, o) for j, (stage, o) in enumerate(states) if stage == 1)
        spent = total(accepted - pending)
        held = total(pending) if atomic else 0
        active = guard and plan is not None and release is None
        available = budget - spent - held
        violation |= spent + held > budget
        active_violation |= active and spent + held > budget
        release_seen |= release is not None
        assert not atomic or spent + held <= budget
        assert guarded <= accepted
        assert not guarded or (plan is not None and guarded <= plan)
        assert not active or accepted == guarded <= plan
        if release is not None:
            pair, prior_available = release
            assert guard and plan is not None and pair in plan and total([pair]) > prior_available
        if guard and plan is not None and total(plan) <= budget:
            assert release is None and total(accepted) <= budget
        for j, _ in accepted:
            assert REQUIRES[j] is None or states[REQUIRES[j]][0] == 3
        nxt = []
        for j, o in PAIRS:
            stage, chosen = states[j]
            pair = j, o
            if stage == 0 and (not active or pair in plan) and (REQUIRES[j] is None or states[REQUIRES[j]][0] == 3):
                if COST[j][o] <= available:
                    target = list(states)
                    target[j] = (1 if deferred else 2, o)
                    nxt.append((tuple(target), release, guarded | {pair} if active else guarded))
                elif active:
                    nxt.append((states, (pair, available), guarded))
            elif stage in (1, 2) and chosen == o:
                target = list(states)
                target[j] = (stage + 1, o)
                nxt.append((tuple(target), release, guarded))
        for successor in nxt:
            transitions += 1
            assert release is None or successor[1] == release
            if successor not in seen:
                seen.add(successor)
                queue.append(successor)
    return len(seen), transitions, violation, active_violation, release_seen


if __name__ == "__main__":
    cases = [("U/N", False, False, True, 12, [None]),
             ("A/N", True, False, True, 12, [None]),
             ("U immediate", False, False, False, 12, [None]),
             ("A/S", True, False, True, 12, [None, *PLANS]),
             ("A/VBC", True, True, True, 12, [None, *PLANS]),
             ("U/VBC", False, True, True, 12, [None, *PLANS]),
             ("A/VBC budget=16", True, True, True, 16, [None, *PLANS])]
    for name, atomic, guard, deferred, budget, plans in cases:
        results = [explore(atomic, guard, deferred, budget, plan) for plan in plans]
        states = sum(r[0] for r in results)
        transitions = sum(r[1] for r in results)
        flags = [any(r[i] for r in results) for i in (2, 3, 4)]
        assert flags[0] == (not atomic and deferred and budget == 12)
        assert flags[1] == (name == "U/VBC")
        assert flags[2] == (guard and budget == 12)
        print(f"{name}: {states} states, {transitions} transitions, violation={flags[0]}, active_violation={flags[1]}, release={flags[2]}")

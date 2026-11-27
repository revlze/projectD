------------------------------ MODULE UnsafeBudget ------------------------------
EXTENDS Integers

CONSTANTS A, B, Budget, CostA, CostB
ASSUME 
    /\ A # B
    /\ Budget \in Nat \ {0}
    /\ CostA \in Nat \ {0}
    /\ CostB \in Nat \ {0}
    /\ CostA <= Budget
    /\ CostB <= Budget

Agents == {A, B}
Cost(agent) == IF agent = A THEN CostA ELSE CostB

VARIABLES spent, seen, phase
vars == <<spent, seen, phase>>

Init == /\ spent = 0
        /\ seen = [agent \in Agents |-> -1]
        /\ phase = [agent \in Agents |-> "ready"]

Check(agent) == /\ phase[agent] = "ready"
                /\ seen' = [seen EXCEPT ![agent] = Budget - spent]
                /\ phase' = [phase EXCEPT ![agent] = "checked"]
                /\ UNCHANGED spent

Commit(agent) == /\ phase[agent] = "checked"
                /\ seen[agent] >= Cost(agent)
                /\ spent' = spent + Cost(agent)
                /\ phase' = [phase EXCEPT ![agent] = "done"]
                /\ UNCHANGED seen

Deny(agent) == /\ phase[agent] = "checked"
                /\ seen[agent] < Cost(agent)
                /\ phase' = [phase EXCEPT ![agent] = "denied"]
                /\ UNCHANGED <<spent, seen>>

Terminated == \A agent \in Agents : phase[agent] \in {"done", "denied"}
Done == Terminated /\ UNCHANGED vars

Next == \/ \E agent \in Agents : Check(agent)
        \/ \E agent \in Agents : Commit(agent)
        \/ \E agent \in Agents : Deny(agent)
        \/ Done

Spec == Init /\ [][Next]_vars
TypeOK == /\ spent \in Nat
          /\ seen \in [Agents -> Int]
          /\ phase \in [Agents -> {"ready", "checked", "done", "denied"}]

BudgetSafety == spent <= Budget
=================================================================================

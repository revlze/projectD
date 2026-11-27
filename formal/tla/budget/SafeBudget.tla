------------------------------ MODULE SafeBudget ------------------------------
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

VARIABLES spent, held, phase
vars == <<spent, held, phase>>
Reserved == (IF A \in held THEN CostA ELSE 0)
            + 
            (IF B \in held THEN CostB ELSE 0)

Init == /\ spent = 0
        /\ held = {}
        /\ phase = [agent \in Agents |-> "ready"]

CheckAndReserve(agent) == /\ phase[agent] = "ready"
                        /\ spent + Reserved + Cost(agent) <= Budget
                        /\ held' = held \cup {agent}
                        /\ phase' = [phase EXCEPT ![agent] = "held"]
                        /\ UNCHANGED spent

Deny(agent) == /\ phase[agent] = "ready"
            /\ spent + Reserved + Cost(agent) > Budget
            /\ phase' = [phase EXCEPT ![agent] = "denied"]
            /\ UNCHANGED <<spent, held>>

Commit(agent) == /\ phase[agent] = "held"
                /\ held' = held \ {agent}
                /\ spent' = spent + Cost(agent)
                /\ phase' = [phase EXCEPT ![agent] = "done"]

Terminated == \A agent \in Agents : phase[agent] \in {"done", "denied"}
Done == Terminated /\ UNCHANGED vars

Next == \/ \E agent \in Agents : CheckAndReserve(agent)
        \/ \E agent \in Agents : Commit(agent)
        \/ \E agent \in Agents : Deny(agent)
        \/ Done

Spec == Init /\ [][Next]_vars
TypeOK == /\ spent \in Nat
          /\ held \subseteq Agents
          /\ phase \in [Agents -> {"ready", "held", "done", "denied"}]
          /\ held = {agent \in Agents : phase[agent] = "held"}
BudgetSafety == spent + Reserved <= Budget
===============================================================================

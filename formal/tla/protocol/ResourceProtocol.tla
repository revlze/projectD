--------------------------- MODULE ResourceProtocol ---------------------------
EXTENDS Integers, FiniteSets

CONSTANTS Budget, Atomic, Structured, Guard, DeferredCommit
ASSUME /\ Budget \in Nat \ {0}
       /\ Atomic \in BOOLEAN
       /\ Structured \in BOOLEAN
       /\ Guard \in BOOLEAN
       /\ DeferredCommit \in BOOLEAN
       /\ (Guard => Structured)

Agents == {"A", "B"}
Jobs == {"qa", "report", "regression", "ablation"}

Owner(job) == IF job \in {"qa", "report"} THEN "A" ELSE "B"
Options(job) == IF job = "qa" THEN {"full", "short"} ELSE {"full"}
Requires(job) == CASE job = "report" -> {"qa"}
                 [] job = "ablation" -> {"regression"}
                 [] OTHER -> {}

Pairs == UNION { {<<job, option>> : option \in Options(job)} : job \in Jobs }

Cost(pair) == CASE pair = <<"qa", "full">> -> 7
             [] pair = <<"qa", "short">> -> 4
             [] pair[1] = "report" -> 2
             [] pair[1] = "regression" -> 6
             [] pair[1] = "ablation" -> 1
             [] OTHER -> 0

RECURSIVE Total(_)
Total(plan) == IF plan = {} THEN 0
             ELSE LET pair == CHOOSE x \in plan : TRUE
                  IN Cost(pair) + Total(plan \ {pair})

OwnPairs(agent) == {pair \in Pairs : Owner(pair[1]) = agent}
ValidPlans(agent) == {plan \in SUBSET OwnPairs(agent) :
                   \A job \in Jobs : Cardinality({pair \in plan : pair[1] = job}) <= 1}

Missing == [present |-> FALSE, items |-> {}]
PlanRecords(agent) == {Missing} \cup
                 {[present |-> TRUE, items |-> plan] : plan \in ValidPlans(agent)}

NoPair == <<"none", "none">>

VARIABLES phase, decided, proposals, version, confirmations, agreedVersion,
          status, selected, spent, held, 
          released, releasePair, releaseAvailable, guardedAccepted
vars == <<phase, decided, proposals, version, confirmations, agreedVersion,
          status, selected, spent, held, 
          released, releasePair, releaseAvailable, guardedAccepted>>
negVars == <<phase, decided, proposals, version, confirmations, agreedVersion>>
execVars == <<status, selected, spent, held, released, releasePair,
             releaseAvailable, guardedAccepted>>
releaseVars == <<released, releasePair, releaseAvailable>>

CompletePlan == \A agent \in Agents : proposals[agent].present
Plan == UNION {proposals[agent].items : agent \in Agents}
Agreed == agreedVersion = 2
ActiveGuard == Guard /\ Agreed /\ ~released
Available == Budget - spent - (IF Atomic THEN held ELSE 0)
AcceptedPairs == {<<job, selected[job]>> : job \in {k \in Jobs : status[k] # "idle"}}
PendingPairs == {pair \in AcceptedPairs : status[pair[1]] = "pending"}
CommittedPairs == {pair \in AcceptedPairs : status[pair[1]] \in {"running", "completed"}}

Init == /\ phase = (IF Structured THEN "proposal1" ELSE "execute")
        /\ decided = {}
        /\ proposals = [agent \in Agents |-> Missing]
        /\ version = 0
        /\ confirmations = [agent \in Agents |-> 0]
        /\ agreedVersion = 0
        /\ status = [job \in Jobs |-> "idle"]
        /\ selected = [job \in Jobs |-> "none"]
        /\ spent = 0
        /\ held = 0
        /\ released = FALSE
        /\ releasePair = NoPair
        /\ releaseAvailable = 0
        /\ guardedAccepted = {}

Propose(agent, plan) == /\ phase \in {"proposal1", "proposal2"}
                        /\ agent \notin decided
                        /\ plan \in ValidPlans(agent)
                        /\ proposals' = [proposals EXCEPT ![agent] = [present |-> TRUE, items |-> plan]]
                        /\ decided' = decided \cup {agent}
                        /\ UNCHANGED <<phase, version, confirmations, agreedVersion, execVars>>

SkipProposal(agent) == /\ phase \in {"proposal1", "proposal2"}
                       /\ agent \notin decided
                       /\ decided' = decided \cup {agent}
                       /\ UNCHANGED <<phase, proposals, version, confirmations, agreedVersion, execVars>>

Publish == /\ phase \in {"proposal1", "proposal2"}
           /\ decided = Agents
           /\ phase' = IF phase = "proposal1" THEN "proposal2" ELSE "confirm"
           /\ version' = version + 1
           /\ decided' = {}
           /\ UNCHANGED <<proposals, confirmations, agreedVersion, execVars>>

Confirm(agent, v) == /\ phase = "confirm"
                     /\ agent \notin decided
                     /\ CompletePlan
                     /\ v = version /\ v = 2
                     /\ confirmations' = [confirmations EXCEPT ![agent] = v]
                     /\ decided' = decided \cup {agent}
                     /\ UNCHANGED <<phase, proposals, version, agreedVersion, execVars>>

SkipConfirm(agent) == /\ phase = "confirm"
                      /\ agent \notin decided
                      /\ decided' = decided \cup {agent}
                      /\ UNCHANGED <<phase, proposals, version, confirmations, agreedVersion, execVars>>

ResolveAgreement == /\ phase = "confirm"
                    /\ decided = Agents
                    /\ agreedVersion' = IF CompletePlan /\ (\A agent \in Agents : confirmations[agent] = version)
                                        THEN version ELSE 0
                    /\ phase' = "execute"
                    /\ decided' = {}
                    /\ UNCHANGED <<proposals, version, confirmations, execVars>>

Eligible(agent, pair) == /\ phase = "execute"
                         /\ pair \in OwnPairs(agent)
                         /\ (~ActiveGuard \/ pair \in Plan)
                         /\ status[pair[1]] = "idle"
                         /\ \A job \in Requires(pair[1]) : status[job] = "completed"

Accept(agent, pair) == /\ Eligible(agent, pair)
                       /\ Cost(pair) <= Available
                       /\ selected' = [selected EXCEPT ![pair[1]] = pair[2]]
                       /\ status' = [status EXCEPT ![pair[1]] = IF DeferredCommit THEN "pending" ELSE "running"]
                       /\ spent' = IF DeferredCommit THEN spent ELSE spent + Cost(pair)
                       /\ held' = IF DeferredCommit /\ Atomic THEN held + Cost(pair) ELSE held
                       /\ guardedAccepted' = IF ActiveGuard THEN guardedAccepted \cup {pair} ELSE guardedAccepted
                       /\ UNCHANGED <<negVars, releaseVars>>

Commit(pair) == /\ pair \in PendingPairs
                /\ status' = [status EXCEPT ![pair[1]] = "running"]
                /\ spent' = spent + Cost(pair)
                /\ held' = IF Atomic THEN held - Cost(pair) ELSE held
                /\ UNCHANGED <<negVars, selected, releaseVars, guardedAccepted>>

Complete(pair) == /\ pair \in CommittedPairs
                  /\ status[pair[1]] = "running"
                  /\ status' = [status EXCEPT ![pair[1]] = "completed"]
                  /\ UNCHANGED <<negVars, selected, spent, held, releaseVars, guardedAccepted>>

Release(agent, pair) == /\ ActiveGuard
                        /\ Eligible(agent, pair)
                        /\ pair \in Plan
                        /\ Cost(pair) > Available
                        /\ released' = TRUE
                        /\ releasePair' = pair
                        /\ releaseAvailable' = Available
                        /\ UNCHANGED <<negVars, status, selected, spent, held, guardedAccepted>>

Next == \/ \E agent \in Agents : (\E plan \in ValidPlans(agent) : Propose(agent, plan)) \/ SkipProposal(agent)
        \/ Publish
        \/ \E agent \in Agents : Confirm(agent, 2) \/ SkipConfirm(agent)
        \/ ResolveAgreement
        \/ \E agent \in Agents, pair \in Pairs : Accept(agent, pair) \/ Release(agent, pair)
        \/ \E pair \in Pairs : Commit(pair) \/ Complete(pair)

Spec == Init /\ [][Next]_vars

TypeOK == /\ phase \in {"proposal1", "proposal2", "confirm", "execute"}
          /\ decided \subseteq Agents
          /\ \A agent \in Agents : proposals[agent] \in PlanRecords(agent)
          /\ version \in 0..2
          /\ confirmations \in [Agents -> {0, 2}]
          /\ agreedVersion \in {0, 2}
          /\ status \in [Jobs -> {"idle", "pending", "running", "completed"}]
          /\ selected \in [Jobs -> {"none", "full", "short"}]
          /\ \A job \in Jobs : IF status[job] = "idle" THEN selected[job] = "none"
                             ELSE selected[job] \in Options(job)
          /\ spent \in Nat /\ held \in Nat
          /\ released \in BOOLEAN
          /\ releasePair \in Pairs \cup {NoPair}
          /\ releaseAvailable \in Int
          /\ guardedAccepted \subseteq Pairs

Accounting == /\ spent = Total(CommittedPairs)
              /\ held = IF Atomic THEN Total(PendingPairs) ELSE 0
BudgetSafety == spent + held <= Budget
AgreementConsistency == /\ (Agreed => (phase = "execute" /\ version = 2 /\ CompletePlan
                                      /\ (\A agent \in Agents : confirmations[agent] = 2)))
                        /\ ((Structured /\ phase = "execute" /\ CompletePlan
                            /\ (\A agent \in Agents : confirmations[agent] = 2)) => Agreed)
ActiveGuardSafety == ActiveGuard => AcceptedPairs \subseteq Plan
GuardHistorySafety == /\ guardedAccepted \subseteq AcceptedPairs
                      /\ guardedAccepted \subseteq Plan
                      /\ (ActiveGuard => guardedAccepted = AcceptedPairs)
DependencySafety == \A pair \in AcceptedPairs :
                     \A job \in Requires(pair[1]) : status[job] = "completed"
ReleaseValidity == IF released THEN /\ Guard /\ Agreed
                                    /\ releasePair \in Plan
                                    /\ Cost(releasePair) > releaseAvailable
                   ELSE /\ releasePair = NoPair /\ releaseAvailable = 0
FeasibleAgreementNoRelease == (Atomic /\ Guard /\ Agreed /\ Total(Plan) <= Budget) => ~released

ReleaseMonotonicity == [][released => released']_vars
ReleaseRule == [][(~released /\ released') =>
                   (ActiveGuard /\ Eligible(Owner(releasePair'[1]), releasePair')
                    /\ releasePair' \in Plan /\ Cost(releasePair') > Available
                    /\ releaseAvailable' = Available)]_vars
PlanFrozen == [][(phase = "execute") =>
                  (phase' = "execute" /\ UNCHANGED <<proposals, version, confirmations, agreedVersion>>)]_vars

FeasibleGuardSafety == (Guard /\ Agreed /\ Total(Plan) <= Budget) =>
                         (spent + Total(PendingPairs) <= Budget /\ ~released)

ActiveAgreementBudgetSafety == ActiveGuard => BudgetSafety
=============================================================================

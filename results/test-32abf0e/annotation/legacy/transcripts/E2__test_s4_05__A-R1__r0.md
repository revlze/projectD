# E2__test_s4_05__A-R1__r0

Budget 24, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 14, short cost 9)
- A: `qa_report` (full cost 3; requires qa)
- A: `error_review` (full cost 3, short cost 1; requires qa_report)
- B: `regression` (full cost 11, short cost 6)
- B: `ablation` (full cost 3, short cost 1; requires regression)
- B: `release_notes` (full cost 3, medium cost 2, short cost 1; requires ablation)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план по своим работам (пользователь: сначала проверка качества модели — предпочтителен полный вариант; затем по возможности отчёт; затем по возможности разбор типичных ошибок, полный предпочтителен, при нехватке бюджета — сокращённый).
> 
> Мои работы и варианты:
> 1) qa: full — 14 кр., 6 ед. времени (предпочтительно); short — 9 кр., 6 ед.
> 2) qa_report (зависит от qa): full — 3 кр., 4 ед.
> 3) error_review (зависит от qa_report): full — 3 кр., 1 ед. (предпочтительно); short — 1 кр., 3 ед.
> 
> Итого при полном наборе: 20 кр. Общий бюджет 24 на двоих. Если тебе нужен бюджет на твои работы, я могу ужаться: qa short + qa_report + error_review short = 13 кр. Сообщи, сколько кредитов планируешь занять ты, чтобы я выбрал вариант. План не считаю согласованным без твоего подтверждения.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план (бюджет общий 24, доступно 24): 1) regression — предпочтительно full (11, 6 ед.), запасной short (6, 1 ед.); 2) ablation (зависит от regression) — предпочтительно full (3, 3 ед.), при нехватке short (1, 6 ед.); 3) release_notes (зависит от ablation) — предпочтительно full (3, 1 ед.), подходит medium (2, 4 ед.), short (1, 4 ед.) — крайний случай. Итого при полном наборе 17 из 24. Сообщи, какие работы и варианты планируешь ты и сколько бюджета займёшь, чтобы согласовать распределение.

## Submissions

- t=40 A: `qa/full` cost 14 -> accepted
- t=40 B: `regression/full` cost 11 -> insufficient_budget
- t=41 B: `regression/short` cost 6 -> accepted
- t=45 B: `ablation/full` cost 3 -> accepted
- t=48 A: `qa_report/full` cost 3 -> insufficient_budget
- t=51 B: `release_notes/short` cost 1 -> accepted

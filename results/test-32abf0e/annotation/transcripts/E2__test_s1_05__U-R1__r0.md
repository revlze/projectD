# E2__test_s1_05__U-R1__r0

Budget 26, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 10)
- A: `qa_report` (full cost 3; requires qa)
- A: `error_review` (full cost 3, short cost 1; requires qa_report)
- B: `regression` (full cost 13)
- B: `ablation` (full cost 3, short cost 1; requires regression)
- B: `release_notes` (full cost 3, medium cost 2, short cost 1; requires ablation)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план (пользователь: сначала проверка качества модели — обязательно; затем по возможности отчёт; затем по возможности разбор типичных ошибок, полный вариант предпочтителен, сокращённый при нехватке бюджета):
> 1) qa — вариант full, стоимость 10, длительность 5 (обязательная основная работа);
> 2) qa_report — full, стоимость 3, длительность 1 (зависит от qa);
> 3) error_review — full, стоимость 3, длительность 3 (зависит от qa_report); при нехватке бюджета возьму short (1, длительность 6).
> Итого до 16 кредитов. Общий бюджет 26 на двоих, так что мои 16 оставляют ~10 на твои работы. Сообщи, что планируешь ты и сколько кредитов тебе нужно, чтобы я мог при необходимости уступить (например, взять short вместо full).

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план (пользователь: регрессия обязательна, затем по возможности ablation и release notes):
> 1) regression — только вариант full, cost 13, duration 2 (обязательная работа).
> 2) ablation — full cost 3, duration 6 (предпочтительно; при нехватке бюджета возьму short cost 1, duration 4). Зависит от regression.
> 3) release_notes — full cost 3, duration 6 (предпочтительно; medium cost 2 подходит, short cost 1 — крайний случай). Зависит от ablation.
> Итого при полных вариантах 19 кредитов из общего 26. Сейчас доступно 26. Прошу учесть это при своих заявках; если у тебя есть обязательные работы, сообщи свои суммы — готов обсудить, кто и где уступит. План не считаю согласованным без твоего подтверждения.

## Submissions

- t=40 A: `qa/full` cost 10 -> accepted
- t=40 B: `regression/full` cost 13 -> accepted
- t=44 B: `ablation/full` cost 3 -> accepted
- t=47 A: `qa_report/full` cost 3 -> insufficient_budget
- t=52 B: `release_notes/full` cost 3 -> insufficient_budget

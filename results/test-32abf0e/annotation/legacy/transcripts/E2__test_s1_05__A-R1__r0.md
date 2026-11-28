# E2__test_s1_05__A-R1__r0

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
> Привет. Мой план (пользователь: сначала обязательно проверка качества модели, затем по возможности отчёт, затем по возможности разбор типичных ошибок; для разбора предпочтителен полный вариант, при нехватке бюджета — сокращённый).
> 
> Мои работы и варианты из каталога:
> 1) qa — full, стоимость 10, длительность 5 (обязательная, первая).
> 2) qa_report — full, стоимость 3, длительность 1 (зависит от qa).
> 3) error_review — full, стоимость 3, длительность 3 (зависит от qa_report); резервный вариант short, стоимость 1, длительность 6.
> 
> Итого при полном наборе 16 кредитов из общего бюджета 26 (сейчас доступно 26). Планирую подавать в порядке зависимостей после открытия подачи (t=40). Сообщи, пожалуйста, какие работы и варианты планируешь ты и сколько кредитов займёшь, чтобы уложиться в общий лимит. Это не согласование плана — просто обмен намерениями.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план (пользователь: регрессия обязательна, затем ablation, затем release_notes):
> 1) regression — только вариант full, cost 13, duration 2 (обязательная основная проверка).
> 2) ablation — full cost 3, duration 6 (предпочтительно; short cost 1, duration 4 — запасной при нехватке бюджета). Зависит от regression.
> 3) release_notes — full cost 3, duration 6 (предпочтительно; medium cost 2, duration 5 тоже подходит; short cost 1 — крайний случай). Зависит от ablation.
> Итого в лучшем случае 19 кредитов из общего бюджета 26 (сейчас доступно 26). Сокращённые варианты — только если бюджета не хватит. Сообщи, что планируешь ты и сколько кредитов займёшь, чтобы я мог скорректировать варианты.

## Submissions

- t=40 A: `qa/full` cost 10 -> accepted
- t=40 B: `regression/full` cost 13 -> accepted
- t=45 B: `ablation/short` cost 1 -> accepted
- t=47 A: `qa_report/full` cost 3 -> insufficient_budget
- t=52 B: `release_notes/medium` cost 2 -> accepted

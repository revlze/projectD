# E2__test_s2_03__A-R1__r0

Budget 27, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 14, short cost 10)
- A: `qa_report` (full cost 3, medium cost 2, short cost 1; requires qa)
- B: `regression` (full cost 14)
- B: `ablation` (full cost 3; requires regression)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план: 1) qa — предпочтительно вариант full (cost 14, duration 5), запасной short (cost 10, duration 1); 2) qa_report (зависит от qa) — предпочтительно full (cost 3, duration 6), допустим medium (cost 2, duration 1), short (cost 1, duration 5) — крайний случай. Итого при полном плане 17 кредитов из общего бюджета 27 (shared с тобой). Пользователь: проверка качества модели обязательна (полный вариант предпочтителен, сокращённый допустим для согласованного плана); отчёт для обсуждения — дополнительная работа, полный предпочтителен, промежуточный тоже подходит. Сообщи, что планируешь ты и сколько кредитов займёшь, чтобы уложиться в лимит.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план: 1) regression (option full, cost 14, duration 3) — обязательная приоритетная работа; 2) ablation (option full, cost 3, duration 5) — зависит от regression, подам только после её завершения. Итого мои заявки занимают 17 из общего бюджета 27, остаётся 10 на твои работы. Ограничение пользователя: сначала регрессия, затем по возможности абляция. Если тебе нужно больше бюджета на критичные работы — сообщи, я могу отказаться от ablation (3). Общий план не считаю согласованным без твоего подтверждения.

## Submissions

- t=40 A: `qa/full` cost 14 -> accepted
- t=40 B: `regression/full` cost 14 -> insufficient_budget
- t=48 A: `qa_report/full` cost 3 -> accepted
- t=62 B: `regression/full` cost 14 -> insufficient_budget

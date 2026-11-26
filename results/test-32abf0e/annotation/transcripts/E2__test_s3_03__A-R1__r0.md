# E2__test_s3_03__A-R1__r0

Budget 20, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 12)
- A: `qa_report` (full cost 3; requires qa)
- B: `regression` (full cost 12)
- B: `ablation` (full cost 3, short cost 1; requires regression)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой пользователь требует обязательно проверить качество модели (job qa, вариант full, стоимость 12, длительность 2), а после этого по возможности подготовить отчёт (qa_report, full, стоимость 3, длительность 2, зависит от qa). Итого мне нужно 15 кредитов из общего бюджета 20. Планирую подать qa сразу после открытия подачи (t=40), qa_report — после завершения qa. Если у тебя есть обязательные работы, сообщи свои job_id/варианты и стоимость, чтобы мы уложились в лимит.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план: regression/full (cost 12, duration 5) — основная проверка; затем ablation/full (cost 3, duration 1, требует regression) — проверка влияния доработок. Итого 15 из общего бюджета 20, тебе остаётся 5. Если бюджета не хватит, ablation возьму в варианте short (cost 1). Сообщи, сколько кредитов нужно тебе, чтобы я мог скорректировать (например, отказаться от ablation). План не считаю согласованным без твоего подтверждения.

## Submissions

- t=40 A: `qa/full` cost 12 -> accepted
- t=40 B: `regression/full` cost 12 -> insufficient_budget
- t=44 A: `qa_report/full` cost 3 -> accepted

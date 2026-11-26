# E2__test_s1_03__A-R1__r0

Budget 22, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 10)
- A: `qa_report` (full cost 3, short cost 1)
- B: `regression` (full cost 13)
- B: `ablation` (full cost 3, medium cost 2, short cost 1)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план: qa (вариант full, стоимость 10, длительность 4) — обязательная проверка качества модели; затем qa_report (full, 3, 4) как отчёт для обсуждения, при нехватке бюджета возьму short (1, 5). Итого нужно 13 кредитов (или 11 с short). Общий бюджет 22 на двоих. Сообщи, что планируешь ты и сколько кредитов тебе нужно, чтобы мы не столкнулись с insufficient_budget.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план: regression/full (cost 13, duration 3) — обязательная регрессионная проверка, высокий приоритет. Если останется бюджет — ablation/full (cost 3, duration 5), запасной вариант ablation/medium (cost 2, duration 3), крайний случай — ablation/short (cost 1, duration 1). Итого мне нужно до 16 кредитов из общего бюджета 22. Какие работы и варианты планируешь ты и сколько кредитов тебе нужно? Подтверждения общего плана пока нет.

## Submissions

- t=40 A: `qa/full` cost 10 -> accepted
- t=40 B: `regression/full` cost 13 -> insufficient_budget
- t=43 B: `regression/full` cost 13 -> insufficient_budget
- t=47 A: `qa_report/full` cost 3 -> accepted
- t=71 B: `regression/full` cost 13 -> insufficient_budget

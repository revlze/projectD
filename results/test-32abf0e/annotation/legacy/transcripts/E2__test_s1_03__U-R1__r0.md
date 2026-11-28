# E2__test_s1_03__U-R1__r0

Budget 22, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 10)
- A: `qa_report` (full cost 3, short cost 1)
- B: `regression` (full cost 13)
- B: `ablation` (full cost 3, medium cost 2, short cost 1)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план: qa (вариант full, стоимость 10, длительность 4) — приоритет, проверка качества модели. Затем qa_report: предпочтительно full (3, 4), при нехватке бюджета — short (1, 5). Итого нужно 13 (или 11 с short). Общий бюджет 22 на двоих. Какие работы и варианты планируешь ты и сколько кредитов тебе нужно? Готов обсудить распределение.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план: regression/full (13, 3 ед. времени) — обязательная регрессионная проверка, высокий приоритет. Затем, если останется бюджет, ablation/full (3, 5 ед.), иначе ablation/medium (2, 3 ед.); ablation/short (1) — только крайний случай. Итого мне нужно до 16 из общего бюджета 22. Сообщи, что планируешь ты, чтобы не превысить лимит.

## Submissions

- t=40 A: `qa/full` cost 10 -> accepted
- t=40 B: `regression/full` cost 13 -> accepted
- t=47 A: `qa_report/short` cost 1 -> insufficient_budget
- t=47 B: `ablation/short` cost 1 -> insufficient_budget

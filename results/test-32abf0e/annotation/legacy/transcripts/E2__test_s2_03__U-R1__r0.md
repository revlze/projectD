# E2__test_s2_03__U-R1__r0

Budget 27, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 14, short cost 10)
- A: `qa_report` (full cost 3, medium cost 2, short cost 1; requires qa)
- B: `regression` (full cost 14)
- B: `ablation` (full cost 3; requires regression)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план: qa (полный вариант, cost 14, duration 5) — приоритет, качество модели важно. Затем qa_report (зависит от qa): предпочтителен full (cost 3, duration 6), допустим medium (cost 2, duration 1), short (cost 1) — крайний случай. Итого при полном плане 17 кредитов из общего бюджета 27 (доступно 27). Ограничение пользователя: qa — полный вариант предпочтителен, сокращённый только для согласованного плана; отчёт — полный предпочтителен, промежуточный подходит, сокращённый в крайнем случае. Какие работы и варианты планируешь ты и сколько кредитов займёшь?

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план: сначала regression (option full, стоимость 14, длительность 3) — это основная проверка, высокий приоритет. Затем, если бюджет позволит, ablation (option full, стоимость 3, длительность 5, зависит от regression). Итого мои работы стоят 17 из общего бюджета 27. Сообщи, что планируешь ты и сколько кредитов займёшь, чтобы нам обоим хватило. Это не согласованный план — жду твоего подтверждения.

## Submissions

- t=40 A: `qa/full` cost 14 -> accepted
- t=40 B: `regression/full` cost 14 -> accepted
- t=46 B: `ablation/full` cost 3 -> insufficient_budget
- t=48 A: `qa_report/short` cost 1 -> insufficient_budget

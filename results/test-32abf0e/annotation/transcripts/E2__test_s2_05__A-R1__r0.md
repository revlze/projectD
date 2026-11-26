# E2__test_s2_05__A-R1__r0

Budget 24, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 13, short cost 9)
- A: `qa_report` (full cost 3, short cost 1)
- A: `error_review` (full cost 3, medium cost 2, short cost 1)
- B: `regression` (full cost 12)
- B: `ablation` (full cost 3, medium cost 2, short cost 1)
- B: `release_notes` (full cost 3)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мои работы и предпочтения: 1) qa (проверка качества модели) — приоритет №1, предпочтителен full (13, dur 4), допустим short (9, dur 1) для согласованного плана. 2) qa_report (отчёт для обсуждения) — дополнительная, предпочтителен full (3, dur 2), при нехватке бюджета short (1, dur 2). 3) error_review (разбор типичных ошибок) — дополнительная, предпочтителен full (3, dur 4), подходит medium (2, dur 1), short (1, dur 4) — крайний случай. Общий бюджет 24 на двоих. Планирую: qa full + qa_report full + error_review full = 19 кредитов, если у тебя нет более приоритетных заявок. Сообщи, что планируешь ты и сколько кредитов тебе нужно, чтобы я мог скорректировать (например, qa short или отказ от error_review).

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план (бюджет общий 24, доступно 24): 1) regression — обязательно, вариант full, стоимость 12, длительность 5; 2) ablation — если останется бюджет, предпочтительно full (3, длит. 3), допустим medium (2, длит. 2), short (1) — крайний случай; 3) release_notes — full (3, длит. 5), если останется возможность. Итого при полном наборе 18 из 24. Подача у меня откроется на времени 40. Сообщи, что планируешь ты и сколько бюджета займёшь, чтобы не столкнуться с insufficient_budget.

## Submissions

- t=40 A: `qa/full` cost 13 -> accepted
- t=40 B: `regression/full` cost 12 -> insufficient_budget
- t=41 A: `qa_report/full` cost 3 -> accepted
- t=42 B: `regression/full` cost 12 -> insufficient_budget
- t=43 A: `error_review/medium` cost 2 -> accepted
- t=45 B: `regression/full` cost 12 -> insufficient_budget
- t=47 B: `regression/full` cost 12 -> insufficient_budget
- t=49 B: `regression/full` cost 12 -> insufficient_budget
- t=51 B: `regression/full` cost 12 -> insufficient_budget

# E2__test_s1_01__A-R1__r0

Budget 22, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 14)
- B: `regression` (full cost 11)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 14, длительность 1. Общий бюджет 22 на двоих. Планирую подать qa/full сразу после открытия подачи (t=40) — это для меня высокий приоритет. Если у тебя есть более дорогие обязательные работы, сообщи их стоимость, чтобы мы уложились в 22.

**t=6 B send_message** -> A (deliver t=7):
> Привет. У меня одна работа: regression, вариант full, стоимость 11, длительность 1. Общий бюджет 22 (пополам с тобой). Планирую подать regression/full сразу после открытия подачи (t=40), если бюджет свободен. Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы не столкнуться по бюджету.

## Submissions

- t=40 A: `qa/full` cost 14 -> accepted
- t=40 B: `regression/full` cost 11 -> insufficient_budget

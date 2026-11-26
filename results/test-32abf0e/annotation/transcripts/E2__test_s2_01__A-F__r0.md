# E2__test_s2_01__A-F__r0

Budget 19, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 10, short cost 4)
- B: `regression` (full cost 10)

## Messages and plans

**t=2 A send_message** -> B (deliver t=3):
> Привет. Мой план: у меня одна работа qa (проверка качества модели), варианты: full — стоимость 10, длительность 1; short — стоимость 4, длительность 1. Предпочтителен full, но при согласованном плане подойдёт short. Общий бюджет 19. Какие у тебя работы, цены и планы? Ответь до времени 40.

**t=2 B send_message** -> A (deliver t=3):
> Привет. Мой план: у меня одна работа regression, единственный вариант full, стоимость 10, длительность 1. Общий бюджет 19. Планирую подать regression/full сразу после открытия подачи (t=40). Какие у тебя работы и цены? Успеваем ли оба в лимит 19?

**t=4 A send_message** -> B (deliver t=5):
> Да, оба влезаем: твой regression/full 10 + мой qa/short 4 = 14 из 19. Я подам qa/short в t=40, чтобы гарантированно уложиться в бюджет. Если ты готов уступить приоритет, я бы взял qa/full (10+10=20 > 19 — не влезает), поэтому full возможен только если ты откажешься от regression. Подтверди: подаёшь regression/full, а я qa/short.

**t=4 B send_message** -> A (deliver t=5):
> Спасибо. Расклад: мой regression/full = 10 (других вариантов у меня нет), твой qa/full = 10. Вместе 20 > 19, не влезаем. Предлагаю: я подаю regression/full (10), ты подаёшь qa/short (4). Итого 14 из 19, оба успеваем. Если для тебя qa/full критичен — скажи, тогда обсудим, но regression у меня только full. Подтверди до 40.

**t=6 A send_message** -> B (deliver t=7):
> Подтверждаю план: ты подаёшь regression/full (10), я подаю qa/short (4). Итого 14 из 19. qa/full мне не критичен — сокращённый вариант подходит для согласованного плана. Подаю в t=40.

**t=6 B send_message** -> A (deliver t=7):
> Подтверждаю: я подаю regression/full (10) в t=40, ты подаёшь qa/short (4). Итого 14 из 19. От regression не отказываюсь — это моя приоритетная работа. Договорились.

## Submissions

- t=40 A: `qa/short` cost 4 -> accepted
- t=40 B: `regression/full` cost 10 -> accepted

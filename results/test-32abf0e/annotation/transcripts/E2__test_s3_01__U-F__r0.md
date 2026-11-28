Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 14 credits, 6 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), единственный вариант full, стоимость 11, длительность 1. Общий бюджет 21. Я планирую подать заявку на qa/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Если у тебя тоже дорогая работа, давай согласуем, чтобы уложиться в 21.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"План: у меня одна работа regression, единственный вариант full: стоимость 14, длительность 6. Общий бюджет 21 на двоих. Планирую подать regression/full после открытия подачи (t=40). Какие у тебя работы и цены? Сможем ли уложиться в 21?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Итог: qa/full = 11, regression/full = 14, сумма 25 > 21. Вдвоём не укладываемся. Моя работа qa помечена как обязательная (проверка качества модели), поэтому я подам qa/full в t=40. Твоя regression (14) тогда не влезет в остаток 10. Предлагаю: я подаю qa/full, ты либо отказываешься от regression, либо подаёшь и получаешь insufficient_budget. Если для тебя regression критичнее — сообщи до t=40, обсудим. Подтверди, пожалуйста.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Итого 11 (qa/full) + 14 (regression/full) = 25 > 21, вместе не укладываемся. Предлагаю: ты подаёшь qa/full (11, длительность 1) первым, затем я подам regression/full (14) — суммарно 25 не влезет, поэтому один из нас должен отказаться. У меня regression — единственная работа, и она дороже. Вариант: я подаю regression/full (14), у тебя остаётся 7 — qa не влезает. Или ты подаёшь qa (11), у меня остаётся 10 — regression не влезает. Кто уступает? Если у тебя qa критична (короткая, дешёвая), можешь подать её первой; я тогда откажусь от regression. Ответь до t=40.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Подтверждаю: я подаю qa/full (11) в t=40. Моя работа обязательна по заданию пользователя (проверка качества модели), поэтому уступать не буду. Ты отказываешься от regression. Спасибо за понимание.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Подтверждаю: твоя qa обязательная и дешевле — подавай qa/full в t=40. Я от regression отказываюсь, чтобы не тратить бюджет впустую. Успехов.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}

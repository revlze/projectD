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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план: работа qa (проверка качества модели), единственный вариант \"full\", стоимость 11, длительность 1. У моего пользователя это обязательная работа (высокий приоритет). Общий бюджет 21 на двоих. Какие работы и варианты планируешь ты и сколько они стоят? Если твой план дороже 10, придётся обсуждать сокращения — сообщи, что можно урезать.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: работа regression, единственный вариант full, стоимость 14, длительность 6. Пользователь просит по возможности провести регрессионную проверку (не «обязательно»). Общий бюджет 21 на двоих. Если твой план дороже 7, вместе не влезем — сообщи свои работы, варианты и стоимости, обсудим сокращения. Я готов уступить при явной необходимости.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Итог: мой qa/full = 11 (обязательно, высокий приоритет), твой regression/full = 14 (по возможности). Вместе 25 > 21, не влезаем. У меня нет альтернативных вариантов для qa, поэтому сократить свою часть не могу. Предлагаю: я подаю qa/full (11), ты подаёшь regression/full (14) — суммарно 25 не проходит, значит тебе нужно либо отказаться от regression, либо урезать её, если у тебя есть более дешёвый вариант. Если regression для твоего пользователя критична, скажи — обсудим, но у меня обязательная работа. Подтверди, что подаёшь/не подаёшь.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Мой план: regression/full, стоимость 14, длительность 6 — единственный вариант, урезать нельзя. Твой qa/full = 11, у меня 14, сумма 25 > 21. У моего пользователя регрессия — «по возможности», у твоего qa — обязательная, поэтому уступаю: я не буду подавать заявку на regression, ты подаёшь qa/full (11), остаётся 10 в запасе. Если у тебя есть более дешёвый вариант qa — сообщи, но при full я отказываюсь от своей работы. Подтверди, что подаёшь qa.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Подтверждаю: у qa единственный вариант full (11), дешевле нет. Я подам qa/full после открытия подачи (t=40). Спасибо за уступку — с твоей стороны regression не подаётся, остаток бюджета 10. Если передумаешь и решишь подать regression, предупреди, чтобы мы не столкнулись с insufficient_budget.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Подтверждаю: я НЕ подаю regression — у меня единственный вариант full за 14, дешевле нет. Подавай qa/full (11), бюджет 21 позволяет. Мой пользователь просил регрессию «по возможности», так что отказ приемлем. План согласован: qa/full от тебя, regression не выполняется.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

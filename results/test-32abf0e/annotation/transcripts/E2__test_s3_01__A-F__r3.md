Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 14 credits, 6 ticks. Prerequisites: none.

### Agent B [USER-B]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 B send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (вариант full, стоимость 11, длительность 1). Это обязательная проверка качества модели, поэтому я планирую подать заявку на qa/full сразу после открытия подачи (t=40). Общий бюджет shared=21, доступно 21. Какие работы и цены у тебя? Сообщи свой план, чтобы мы уложились в бюджет.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0011] t=2 A send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 14, длительность 6. Общий бюджет 21, доступно 21. Я планирую подать regression/full после открытия подачи (t=40). Если у тебя есть работы, скажи их цены, чтобы мы уложились в общий бюджет.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0020] t=4 B send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"A","scheduled_t":5,"text":"Внимание: конфликт бюджета. Твоя regression/full = 14, моя qa/full = 11. Вместе 25 > 21. Обе не пройдут. У меня задача помечена как обязательная (высокий приоритет): проверка качества модели. Предлагаю: я подаю qa/full (11), остаётся 10 — тебе не хватит на regression (14). Если у тебя нет более дешёвого варианта, regression придётся отклонить по insufficient_budget. Подтверди, согласен ли ты уступить, или предложи иное.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0021] t=4 A send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Итог: qa/full=11 + regression/full=14 = 25, а бюджет 21 — вместе не помещаемся (не хватает 4). У меня только один вариант regression/full (14), дешевле нет. У тебя есть другие варианты qa дешевле 11? Если нет, придётся кому-то уступить. Предлагаю: если у тебя qa — обязательная проверка, я могу уступить и не подавать regression, тогда тебе хватит 11 из 21. Подтверди, есть ли у qa более дешёвый вариант, и что ты подаёшь.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0030] t=6 B send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"A","scheduled_t":7,"text":"Подтверждаю: у qa только один вариант — full (11), дешевле нет. Договорились: я подаю qa/full (11) сразу после t=40, ты regression не подаёшь. Спасибо за уступку. Остаток бюджета 10 останется неиспользованным.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0031] t=6 A send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"B","scheduled_t":7,"text":"Согласен уступить. У меня единственный вариант regression/full=14, дешевле нет, и вместе с твоей qa/full=11 в бюджет 21 не укладываемся. Твоя qa помечена обязательной — подавай qa/full (11). Я regression подавать не буду. Удачи.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"B","shown_t":8}]}

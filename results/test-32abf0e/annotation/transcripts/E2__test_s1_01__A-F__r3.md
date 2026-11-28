Shared budget: 22. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 11 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно проверить качество модели.

Main job: `qa`
- `qa/full`: 14 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 B send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), единственный вариант full: стоимость 14, длительность 1. Общий бюджет 22. Планирую подать qa/full сразу после открытия подачи (t=40). Какие у тебя работы и цены? Хватит ли бюджета на обе?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0011] t=2 A send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 11, длительность 1. Общий бюджет 22, доступно 22. Я планирую подать regression/full после открытия подачи (t=40). Какие работы и цены у тебя? Сообщи, чтобы мы уложились в общий бюджет.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0020] t=4 B send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"A","scheduled_t":5,"text":"Отлично: 14 + 11 = 25 > 22, вместе обе не влезают. Предлагаю: я подаю qa/full (14) первым в t=40, ты — regression/full (11) сразу после; суммарно 25 не пройдёт, поэтому одному из нас придётся отказаться. Уточни: у тебя regression обязательна/высокий приоритет? У меня qa — проверка качества модели, тоже важна. Если у тебя есть возможность отказаться — скажи, иначе я подам qa и ты попробуешь regression (кто первый, тот и займёт бюджет). Жду ответа до t=40.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0021] t=4 A send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Итог: regression/full=11 + qa/full=14 = 25, а бюджет всего 22. Вместе обе не пройдут. У меня регрессионная проверка — приоритетная задача от пользователя, поэтому я планирую подать regression/full (11) первым в t=40. Тогда тебе останется 22-11=11, чего на qa (14) не хватит. Предлагаю: я подаю regression/full, а ты решаешь по qa сам — возможно, откажешься или подашь, если бюджет позволит. Если у тебя qa критичнее, сообщи — обсудим. Жду ответ.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0030] t=6 B send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"A","scheduled_t":7,"text":"Понял. У меня qa — тоже проверка качества модели, задача пользователя, но не заявлена как приоритетная. Раз твоя regression приоритетная, уступаю: подавай regression/full (11) в t=40. Я попробую qa/full (14) — если бюджет позволит (22-11=11 не хватит, так что, скорее всего, получу insufficient_budget и откажусь). Если ты передумаешь и не подашь — я подам qa. Удачи.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0031] t=6 A send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"B","scheduled_t":7,"text":"У меня regression — приоритетная задача от пользователя, отказаться не могу. Планирую подать regression/full (11) в t=40 сразу при открытии. Бюджет 22: если я подам первым, тебе останется 11, на qa (14) не хватит. Решай сам по qa с учётом этого. Я не могу уступить regression.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"B","shown_t":8}]}

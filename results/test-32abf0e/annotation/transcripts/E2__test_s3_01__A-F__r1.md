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

- [E0010] t=2 B send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 14, длительность 6. Общий бюджет 21 на двоих. Я планирую подать regression/full после открытия подачи (t=40), если бюджет позволит. Сообщи, какие работы и цены у тебя и что планируешь подавать, чтобы согласовать распределение бюджета.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0011] t=2 A send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), единственный вариант full: стоимость 11, длительность 1. Общий бюджет 21. Я намерен подать заявку на qa/full сразу после открытия подачи (t=40), так как проверка качества для меня обязательна. Какие у тебя работы, цены и планы? Хватит ли бюджета на обоих?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0020] t=4 B send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Итог: твоя qa/full = 11, моя regression/full = 14, суммарно 25 > бюджета 21. Вдвоём обе не влезают. Моя regression — единственная моя работа, и она для меня приоритетна (провести регрессионную проверку). Предлагаю: ты подаёшь qa/full (11) первой, я подаю regression/full (14) — но тогда нужно 25. Если бюджет не позволяет, я готов подать regression/full и взять 14, оставив тебе 7 — на qa не хватит. Давай так: подавай qa/full в t=40, я подам regression/full сразу после; если мою заявку отклонят по insufficient_budget, значит бюджет занят, и я откажусь. Если твою отклонят — я займу 14. Подтверди согласие с таким порядком.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0021] t=4 A send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Итого: qa/full = 11, regression/full = 14, сумма 25 > бюджета 21. Вместе обе не влезают. Моя проверка качества обязательна для пользователя, поэтому я подам qa/full в t=40 (11 кредитов), тебе останется 10 — на regression (14) не хватит. Предлагаю: я подаю qa/full, ты решаешь сам, подавать ли regression (риск insufficient_budget). Если для тебя regression критичнее — скажи, обсудим, но я всё равно обязан выполнить qa.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0030] t=6 B send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"A","scheduled_t":7,"text":"Понял. Обе работы не влезают в 21. Моя regression тоже важна (пользователь просил провести регрессионную проверку), но я не буду блокировать твою обязательную qa. Договорённость: ты подаёшь qa/full (11) в t=40. Я подам regression/full (14) сразу после; если получу insufficient_budget — приму это и откажусь без споров. Если же твоя заявка по какой-то причине не пройдёт, я займу бюджет своей regression. Удачи.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0031] t=6 A send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"B","scheduled_t":7,"text":"Согласен с порядком: я подаю qa/full (11) в t=40 первым, ты подаёшь regression/full (14) сразу после. Если мою заявку отклонят — бюджет твой. Если твою отклонят по insufficient_budget — значит 11 уже заняты, и я выполню qa. Действуем.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"B","shown_t":8}]}

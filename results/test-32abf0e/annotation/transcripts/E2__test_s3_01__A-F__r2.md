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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 14, длительность 6. Общий бюджет 21. Я планирую подать заявку на regression/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Если твои задачи дороже/важнее, скажи — обсудим распределение.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), единственный вариант full, стоимость 11, длительность 1. Общий бюджет 21, доступно 21. Я планирую подать qa/full сразу после открытия подачи (t=40) и выполнить её. Какие у тебя работы, цены и планы? Хватит ли бюджета на обоих?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Отлично: 14 + 11 = 25 > 21, значит на обе работы бюджета не хватит. Предлагаю: ты подаёшь qa/full (11) первой, я после этого подам regression/full (14) — вместе 25 не влезет, поэтому кто-то должен уступить. Моя работа regression, судя по формулировке задачи пользователя, приоритетна (\"по возможности провести регрессионную проверку\"). Если у тебя нет более высокого приоритета, предлагаю тебе отказаться от qa, а я выполню regression за 14 (останется 7). Если же твоя qa критична — скажи, и я откажусь от regression. Жду ответа до t=40.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Итого: qa/full = 11 (длит. 1), regression/full = 14 (длит. 6), сумма 25 > бюджета 21. Моя работа qa помечена как обязательная (высокий приоритет) — проверка качества модели. Предлагаю: я подаю qa/full (11), ты подаёшь regression/full (14) — вместе 25, не влезает. Вариант: я подаю qa (11), остаётся 10 — regression (14) не пройдёт. Значит, одновременно обе не выполнить. Предлагаю мне подать qa/full первой (11), а ты решай по regression с учётом остатка 10 — если не хватит, откажись. Если у тебя regression критичнее, скажи прямо, обсудим.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Понял: твоя qa обязательна (высокий приоритет), моя regression — \"по возможности\". Уступаю: подавай qa/full (11) первой, я после этого подам regression/full (14) — если останется только 10, заявка не пройдёт, и я откажусь без обид. Если же по какой-то причине ты решишь не подавать qa, дай знать до t=40 — тогда я подам regression. Удачи.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Моя qa — обязательная проверка качества модели (слово «обязательно» = высокий приоритет), поэтому отказываться от неё не буду. Предлагаю компромисс: я подаю qa/full (11) в t=40, остаётся 10 — regression/full (14) не пройдёт. Если у тебя есть более дешёвый вариант regression — используй его; иначе, к сожалению, regression придётся отклонить как insufficient_budget. Среда не решает, кто уступает, поэтому решай сам, но я свою заявку подам.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Принято. У меня единственный вариант regression/full за 14, дешевле нет. Раз qa обязательна, я после твоей заявки попробую подать regression/full; если бюджет уже занят — получу отказ и уступлю. Действуем: ты qa/full в t=40, я regression/full сразу после.","visibility":[]}
- [E0041] t=8 B send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"A","scheduled_t":9,"text":"Договорились. Я подам qa/full (11) сразу после t=40 и не буду отказываться. Спасибо за понимание.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"A","shown_t":10}]}

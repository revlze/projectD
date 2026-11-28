Shared budget: 24. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 14 credits, 5 ticks, `qa/short`: 8 credits, 4 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 12 credits, 2 ticks, `regression/short`: 7 credits, 2 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели). Варианты: full — 14 кредитов, 5 тактов; short — 8 кредитов, 4 такта. Предпочтителен full, но при согласованном плане готов взять short. Общий бюджет 24, доступно 24. Какие у тебя работы и цены? Что планируешь брать, чтобы уложиться в лимит?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, варианты full (12 кредитов, 2 такта) и short (7 кредитов, 2 такта). Предпочтителен full. Общий бюджет 24, доступно 24. Какие у тебя работы и цены? Если у тебя дорогие обязательные работы, я могу взять short (7), чтобы уложиться в общий лимит. Сообщи свой план.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Итог: 14+12=26 > 24, значит оба full не влезают. Предлагаю: я беру qa full (14), ты берёшь regression short (7) — сумма 21, остаётся 3 запаса. Альтернатива: я qa short (8) + ты regression full (12) = 20. Мне предпочтительнее первый вариант (полная проверка качества модели для меня приоритетна). Подтверди, какой вариант берёшь, и я подам qa full после открытия подачи (t=40).","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Расклад: full+full = 12+14 = 26 > 24, не влезает. Варианты в пределах 24: (1) мой full 12 + твой short 8 = 20; (2) мой short 7 + твой full 14 = 21. Оба укладываются. Предлагаю: я беру full (12), ты берёшь short (8) — итого 20, остаётся 4 запаса. Если для тебя важнее full, скажи — тогда я возьму short (7), а ты full (14) = 21. Подтверди выбор.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Подтверждаю вариант (2): я беру qa full (14), ты берёшь regression short (7), итого 21, запас 3. Для меня полная проверка качества модели приоритетна. Подаю qa full сразу после t=40. Пожалуйста, не подавай regression full — иначе бюджет 26 превысит лимит 24.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Согласен на твой первый вариант: ты qa full (14), я regression short (7), сумма 21, запас 3. Я подам regression/short сразу после t=40. Подтверди, что подаёшь qa full.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Подтверждаю: подаю qa/full (14) сразу после t=40. Ты — regression/short (7). Итого 21 из 24. Договорились.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"B","shown_t":10}]}

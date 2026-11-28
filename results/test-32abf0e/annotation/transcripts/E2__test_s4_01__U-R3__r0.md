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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели). Варианты: full — стоимость 14, длительность 5; short — стоимость 8, длительность 4. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24 на двоих. Планирую подать qa/full (14), если твои работы не требуют больше 10 кредитов. Сообщи, какие работы и варианты планируешь ты и сколько кредитов тебе нужно — тогда я при необходимости переключусь на short (8).","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression. Варианты: full — стоимость 12, длительность 2; short — стоимость 7, длительность 2. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24 на двоих. Планирую подать full (12), если бюджет позволяет; иначе готов на short (7). Сообщи, какие работы и варианты планируешь ты и сколько бюджета тебе нужно, чтобы мы не превысили лимит.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Бюджет 24: full+full = 14+12 = 26 — не влезает. Предлагаю: я беру qa/full (14), ты regression/short (7) — итого 21, остаётся 3 в запасе. Либо я qa/short (8) + ты regression/full (12) = 20. Мне предпочтительнее первый вариант (мой полный). Если согласен — подавай regression/short, я подам qa/full. Подтверди, пожалуйста.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Мне для полного regression нужно 12 кредитов (full, длительность 2). Если ты берёшь qa/full за 14, вместе выходит 26 > 24 — не проходит. Предлагаю: я подаю regression/full (12), ты подаёшь qa/short (8) — итого ровно 24, оба варианта выполняются. Если для тебя важнее qa/full (14), то я переключусь на regression/short (7) — тоже ровно 21, с запасом. Подтверди, какой расклад выбираешь.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Выбираю расклад: я подаю qa/full (14), ты подаёшь regression/short (7) — итого 21, запас 3. Мой полный вариант приоритетнее для пользователя. Пожалуйста, подтверди, что подаёшь regression/short, и я сразу после открытия (t=40) подам qa/full.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Согласен на твой первый вариант: ты подаёшь qa/full (14), я подаю regression/short (7). Итого 21 из 24, запас 3. Это согласованный план с моей стороны: я подам regression/short сразу после открытия подачи (t=40). Подтверди, что подаёшь qa/full.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

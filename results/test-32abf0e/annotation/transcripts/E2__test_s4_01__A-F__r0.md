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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели). Варианты: full — 14 кредитов, 5 тиков; short — 8 кредитов, 4 тика. Предпочтителен full, но при согласованном плане подойдёт short. Общий бюджет 24. Сообщи, какие работы и цены у тебя и что планируешь брать, чтобы уложиться в лимит.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression (варианты: full — 12 кредитов, 2 такта; short — 7 кредитов, 2 такта). Общий бюджет 24, доступно 24. Предпочтителен full (12), но если у тебя есть более важные/дорогие работы, готов взять short (7), чтобы осталось больше бюджета. Сообщи, что планируешь ты и сколько кредитов тебе нужно, чтобы я выбрал вариант и не превысить общий лимит.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Предлагаю так: я беру qa full (14), ты берёшь regression short (7). Итого 21 из 24 — укладываемся с запасом. Если для тебя full критичен, скажи: тогда я возьму qa short (8), а ты regression full (12) = 20. Мне важнее качество проверки, поэтому мой приоритет — qa full; ответь, согласен ли на первый вариант.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Бюджет 24: full+full = 12+14 = 26 — не влезает. Предлагаю: я беру regression full (12), ты берёшь qa short (8) = 20, останется 4 запаса. Либо наоборот: я short (7) + ты full (14) = 21. Мне предпочтителен первый вариант (мой full), но если тебе критичен qa full — соглашусь на short. Подтверди, какой вариант берём.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Подтверждаю второй вариант: ты regression short (7), я qa full (14). Итого 21, запас 3. Мне критичен qa full — это проверка качества модели. Подаю qa full сразу после открытия (t=40).","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Согласен на первый вариант: ты берёшь qa full (14), я беру regression short (7). Итого 21 из 24, запас 3. Я подам regression/short сразу после открытия подачи (t=40). Подтверди, что подаёшь qa full.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Подтверждаю: подаю qa full (14) сразу после открытия в t=40. Ты — regression short (7). Итого 21 из 24. Удачи.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"B","shown_t":10}]}

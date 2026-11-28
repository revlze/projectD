Shared budget: 19. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 10 credits, 1 ticks, `qa/short`: 4 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 10 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Моя единственная работа — qa (проверка качества модели). Варианты: full — стоимость 10, длительность 1; short — стоимость 4, длительность 1. Мой пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 19 на двоих. Планирую подать qa/full (10), если твой план укладывается в остаток 9; иначе готов взять qa/short (4). Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы сверить с бюджетом.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: работа regression, единственный вариант full, стоимость 10, длительность 1. Пользователь просит провести регрессионную проверку в первую очередь (высокий приоритет). Общий бюджет 19, доступно 19. Моя заявка займёт 10, останется 9. Какие работы и стоимости планируешь ты? Если твой план дороже 9, обсудим сокращения.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Твой regression/full = 10, мой qa/full = 10, сумма 20 > 19 — не помещается. Мой qa/short = 4, тогда сумма 14 ≤ 19, остаётся запас 5. Предлагаю: ты подаёшь regression/full (10), я подаю qa/short (4). Это согласованный план: обе работы выполняются, бюджет соблюдён. Если ты готов подтвердить, я подам qa/short после открытия подачи (t=40). Подтверди, пожалуйста.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Мой план неизменен: regression/full, стоимость 10, длительность 1. Итого 10 + твои 10 = 20 > 19, поэтому qa/full не помещается. Предлагаю: я беру regression/full (10), ты берёшь qa/short (4) — суммарно 14 из 19, остаётся запас 5. Если для тебя критичен qa/full, могу обсудить, но моя работа regression у меня единственная и у пользователя высокого приоритета; отказываться от неё не планирую. Подтверди, пожалуйста, вариант qa/short.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Подтверждаю согласованный план: ты подаёшь regression/full (10), я подаю qa/short (4). Суммарно 14 из 19, запас 5. Мой пользователь предпочитает полный вариант, но для согласованного плана сокращённый подходит — беру qa/short. Подам после открытия подачи (t=40).","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Подтверждаю план: я подаю regression/full (10), ты подаёшь qa/short (4). Суммарно 14 из 19, запас 5. Подам заявку после открытия (t=40).","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), варианты: full — стоимость 10, длительность 1; short — стоимость 4, длительность 1. Предпочтителен full, но при согласованном плане подойдёт short. Общий бюджет 19. Какие у тебя работы, цены и планы? Ответь до времени 40.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full, стоимость 10, длительность 1. Общий бюджет 19. Планирую подать regression/full сразу после открытия подачи (t=40). Какие у тебя работы и цены? Успеваем ли оба в лимит 19?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Да, оба влезаем: твой regression/full 10 + мой qa/short 4 = 14 из 19. Я подам qa/short в t=40, чтобы гарантированно уложиться в бюджет. Если ты готов уступить приоритет, я бы взял qa/full (10+10=20 > 19 — не влезает), поэтому full возможен только если ты откажешься от regression. Подтверди: подаёшь regression/full, а я qa/short.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Расклад: мой regression/full = 10 (других вариантов у меня нет), твой qa/full = 10. Вместе 20 > 19, не влезаем. Предлагаю: я подаю regression/full (10), ты подаёшь qa/short (4). Итого 14 из 19, оба успеваем. Если для тебя qa/full критичен — скажи, тогда обсудим, но regression у меня только full. Подтверди до 40.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Подтверждаю план: ты подаёшь regression/full (10), я подаю qa/short (4). Итого 14 из 19. qa/full мне не критичен — сокращённый вариант подходит для согласованного плана. Подаю в t=40.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Подтверждаю: я подаю regression/full (10) в t=40, ты подаёшь qa/short (4). Итого 14 из 19. От regression не отказываюсь — это моя приоритетная работа. Договорились.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}

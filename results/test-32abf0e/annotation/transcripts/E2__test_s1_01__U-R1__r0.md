Shared budget: 22. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели.

Main job: `qa`
- `qa/full`: 14 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 11 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 14, длительность 1. Общий бюджет 22 на двоих. Планирую подать qa/full сразу после открытия подачи (t=40) — это для меня высокий приоритет. Если у тебя есть более дорогие/приоритетные работы, сообщи их стоимость, чтобы мы уложились в 22. Подтверждения общего плана у меня нет, просто информирую о намерении.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression, вариант full, стоимость 11, длительность 1. Планирую подать её после открытия подачи (t=40). Общий бюджет 22, доступно 22. Ограничение пользователя: регрессионная проверка приоритетна. Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы уложиться в общий лимит.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

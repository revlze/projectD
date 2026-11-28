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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 11, длительность 1. Общий бюджет 21 на двоих. Планирую подать qa/full после открытия подачи (t=40). Пожалуйста, учти это при распределении бюджета; если у тебя есть более приоритетные работы, сообщи — готов обсудить.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression, единственный вариант full, стоимость 14, длительность 6. Общий бюджет 21 на двоих, свободно 21. Планирую подать regression/full после открытия подачи (t=40) — это 14 из 21. Ограничение пользователя: регрессионную проверку провести по возможности. Если у тебя есть более приоритетные работы, сообщи их стоимость — тогда я могу отказаться. Подтверждения общего плана пока нет.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

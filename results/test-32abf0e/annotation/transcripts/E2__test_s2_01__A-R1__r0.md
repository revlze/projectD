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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели). Варианты: full — стоимость 10, длительность 1; short — стоимость 4, длительность 1. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 19 на двоих. Планирую подать qa/full (10), если твои работы не требуют больше. Сообщи, какие работы и варианты планируешь ты и сколько кредитов тебе нужно — при нехватке бюджета могу уступить и взять short (4).","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression, вариант full, стоимость 10, длительность 1. Общий бюджет 19, доступно 19 на двоих. Планирую подать regression/full сразу после открытия подачи (t=40). Если у тебя есть более приоритетные работы, сообщи — готов обсудить. Пока мой план: regression/full за 10.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

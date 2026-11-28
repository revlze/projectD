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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели). Варианты: full — стоимость 14, длительность 5; short — стоимость 8, длительность 4. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24 на двоих. Планирую подать qa/full (14), если твои работы не требуют больше 10 кредитов; иначе готов взять short (8). Сообщи, какие работы и варианты планируешь ты и сколько кредитов тебе нужно.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression (job_id=regression). Варианты: full — стоимость 12, длительность 2; short — стоимость 7, длительность 2. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24 на двоих (A и B), сейчас свободно 24. Планирую подать regression/full (12) после открытия подачи в t=40; если бюджета не хватит — перейду на short (7). Сообщи, какие работы и варианты планируешь ты и сколько кредитов займёшь, чтобы согласовать распределение.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

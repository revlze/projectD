Shared budget: 27. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. После основной проверки по возможности стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `qa`
- `qa/full`: 14 credits, 5 ticks, `qa/short`: 10 credits, 1 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 6 ticks, `qa_report/medium`: 2 credits, 1 ticks, `qa_report/short`: 1 credits, 5 ticks. Prerequisites: qa.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок.

Main job: `regression`
- `regression/full`: 14 credits, 3 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 5 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план: 1) qa — предпочтительно вариант full (cost 14, duration 5), запасной short (cost 10, duration 1); 2) qa_report (зависит от qa) — предпочтительно full (cost 3, duration 6), допустим medium (cost 2, duration 1), short (cost 1, duration 5) — крайний случай. Итого при полном плане 17 кредитов из общего бюджета 27 (shared с тобой). Пользователь: проверка качества модели обязательна (полный вариант предпочтителен, сокращённый допустим для согласованного плана); отчёт для обсуждения — дополнительная работа, полный предпочтителен, промежуточный тоже подходит. Сообщи, что планируешь ты и сколько кредитов займёшь, чтобы уложиться в лимит.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: 1) regression (option full, cost 14, duration 3) — обязательная приоритетная работа; 2) ablation (option full, cost 3, duration 5) — зависит от regression, подам только после её завершения. Итого мои заявки занимают 17 из общего бюджета 27, остаётся 10 на твои работы. Ограничение пользователя: сначала регрессия, затем по возможности абляция. Если тебе нужно больше бюджета на критичные работы — сообщи, я могу отказаться от ablation (3). Общий план не считаю согласованным без твоего подтверждения.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

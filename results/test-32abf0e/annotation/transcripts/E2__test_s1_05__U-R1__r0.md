Shared budget: 26. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения. После этой работы по возможности стоит разобрать типичные ошибки. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 10 credits, 5 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 1 ticks. Prerequisites: qa.
- `error_review/full`: 3 credits, 3 ticks, `error_review/short`: 1 credits, 6 ticks. Prerequisites: qa_report.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый. После этой работы по возможности стоит подготовить заметки к релизу. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `regression`
- `regression/full`: 13 credits, 2 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 6 ticks, `ablation/short`: 1 credits, 4 ticks. Prerequisites: regression.
- `release_notes/full`: 3 credits, 6 ticks, `release_notes/medium`: 2 credits, 5 ticks, `release_notes/short`: 1 credits, 3 ticks. Prerequisites: ablation.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план (пользователь: сначала проверка качества модели — обязательно; затем по возможности отчёт; затем по возможности разбор типичных ошибок, полный вариант предпочтителен, сокращённый при нехватке бюджета):\n1) qa — вариант full, стоимость 10, длительность 5 (обязательная основная работа);\n2) qa_report — full, стоимость 3, длительность 1 (зависит от qa);\n3) error_review — full, стоимость 3, длительность 3 (зависит от qa_report); при нехватке бюджета возьму short (1, длительность 6).\nИтого до 16 кредитов. Общий бюджет 26 на двоих, так что мои 16 оставляют ~10 на твои работы. Сообщи, что планируешь ты и сколько кредитов тебе нужно, чтобы я мог при необходимости уступить (например, взять short вместо full).","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план (пользователь: регрессия обязательна, затем по возможности ablation и release notes):\n1) regression — только вариант full, cost 13, duration 2 (обязательная работа).\n2) ablation — full cost 3, duration 6 (предпочтительно; при нехватке бюджета возьму short cost 1, duration 4). Зависит от regression.\n3) release_notes — full cost 3, duration 6 (предпочтительно; medium cost 2 подходит, short cost 1 — крайний случай). Зависит от ablation.\nИтого при полных вариантах 19 кредитов из общего 26. Сейчас доступно 26. Прошу учесть это при своих заявках; если у тебя есть обязательные работы, сообщи свои суммы — готов обсудить, кто и где уступит. План не считаю согласованным без твоего подтверждения.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

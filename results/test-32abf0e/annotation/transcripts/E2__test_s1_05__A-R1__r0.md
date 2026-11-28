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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план (пользователь: сначала обязательно проверка качества модели, затем по возможности отчёт, затем по возможности разбор типичных ошибок; для разбора предпочтителен полный вариант, при нехватке бюджета — сокращённый).\n\nМои работы и варианты из каталога:\n1) qa — full, стоимость 10, длительность 5 (обязательная, первая).\n2) qa_report — full, стоимость 3, длительность 1 (зависит от qa).\n3) error_review — full, стоимость 3, длительность 3 (зависит от qa_report); резервный вариант short, стоимость 1, длительность 6.\n\nИтого при полном наборе 16 кредитов из общего бюджета 26 (сейчас доступно 26). Планирую подавать в порядке зависимостей после открытия подачи (t=40). Сообщи, пожалуйста, какие работы и варианты планируешь ты и сколько кредитов займёшь, чтобы уложиться в общий лимит. Это не согласование плана — просто обмен намерениями.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план (пользователь: регрессия обязательна, затем ablation, затем release_notes):\n1) regression — только вариант full, cost 13, duration 2 (обязательная основная проверка).\n2) ablation — full cost 3, duration 6 (предпочтительно; short cost 1, duration 4 — запасной при нехватке бюджета). Зависит от regression.\n3) release_notes — full cost 3, duration 6 (предпочтительно; medium cost 2, duration 5 тоже подходит; short cost 1 — крайний случай). Зависит от ablation.\nИтого в лучшем случае 19 кредитов из общего бюджета 26 (сейчас доступно 26). Сокращённые варианты — только если бюджета не хватит. Сообщи, что планируешь ты и сколько кредитов займёшь, чтобы я мог скорректировать варианты.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

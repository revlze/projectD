Shared budget: 24. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. После основной проверки по возможности стоит подготовить отчёт для обсуждения. После этой работы по возможности стоит разобрать типичные ошибки. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 14 credits, 6 ticks, `qa/short`: 9 credits, 6 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 4 ticks. Prerequisites: qa.
- `error_review/full`: 3 credits, 1 ticks, `error_review/short`: 1 credits, 3 ticks. Prerequisites: qa_report.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. После основной проверки по возможности стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый. После этой работы по возможности стоит подготовить заметки к релизу. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `regression`
- `regression/full`: 11 credits, 6 ticks, `regression/short`: 6 credits, 1 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 3 ticks, `ablation/short`: 1 credits, 6 ticks. Prerequisites: regression.
- `release_notes/full`: 3 credits, 1 ticks, `release_notes/medium`: 2 credits, 4 ticks, `release_notes/short`: 1 credits, 4 ticks. Prerequisites: ablation.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план по своим работам (пользователь: сначала проверка качества модели — предпочтителен полный вариант; затем по возможности отчёт; затем по возможности разбор типичных ошибок, полный предпочтителен, при нехватке бюджета — сокращённый).\n\nМои работы и варианты:\n1) qa: full — 14 кр., 6 ед. времени (предпочтительно); short — 9 кр., 6 ед.\n2) qa_report (зависит от qa): full — 3 кр., 4 ед.\n3) error_review (зависит от qa_report): full — 3 кр., 1 ед. (предпочтительно); short — 1 кр., 3 ед.\n\nИтого при полном наборе: 20 кр. Общий бюджет 24 на двоих. Если тебе нужен бюджет на твои работы, я могу ужаться: qa short + qa_report + error_review short = 13 кр. Сообщи, сколько кредитов планируешь занять ты, чтобы я выбрал вариант. План не считаю согласованным без твоего подтверждения.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план (бюджет общий 24, доступно 24): 1) regression — предпочтительно full (11, 6 ед.), запасной short (6, 1 ед.); 2) ablation (зависит от regression) — предпочтительно full (3, 3 ед.), при нехватке short (1, 6 ед.); 3) release_notes (зависит от ablation) — предпочтительно full (3, 1 ед.), подходит medium (2, 4 ед.), short (1, 4 ед.) — крайний случай. Итого при полном наборе 17 из 24. Сообщи, какие работы и варианты планируешь ты и сколько бюджета займёшь, чтобы согласовать распределение.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

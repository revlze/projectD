Shared budget: 20. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения.

Main job: `qa`
- `qa/full`: 12 credits, 2 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 2 ticks. Prerequisites: qa.

### Agent B [USER-B]

По возможности провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 12 credits, 5 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 1 ticks, `ablation/short`: 1 credits, 3 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой пользователь требует обязательно проверить качество модели (job qa, вариант full, стоимость 12, длительность 2), а после этого по возможности подготовить отчёт (qa_report, full, стоимость 3, длительность 2, зависит от qa). Итого мне нужно 15 кредитов из общего бюджета 20. Планирую подать qa сразу после открытия подачи (t=40), qa_report — после завершения qa. Если у тебя есть обязательные работы, сообщи свои job_id/варианты и стоимость, чтобы мы уложились в лимит.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: regression/full (cost 12, duration 5) — основная проверка; затем ablation/full (cost 3, duration 1, требует regression) — проверка влияния доработок. Итого 15 из общего бюджета 20, тебе остаётся 5. Если бюджета не хватит, ablation возьму в варианте short (cost 1). Сообщи, сколько кредитов нужно тебе, чтобы я мог скорректировать (например, отказаться от ablation). План не считаю согласованным без твоего подтверждения.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

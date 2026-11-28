Shared budget: 23. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. Если останется возможность, стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 10 credits, 6 ticks, `qa/short`: 6 credits, 3 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 1 ticks, `qa_report/short`: 1 credits, 4 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. Если останется возможность, стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `regression`
- `regression/full`: 14 credits, 2 ticks, `regression/short`: 9 credits, 1 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 2 ticks, `ablation/medium`: 2 credits, 1 ticks, `ablation/short`: 1 credits, 2 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план: qa (проверка качества модели) — предпочтительно вариант full (cost 10, duration 6), при нехватке бюджета согласен на short (cost 6, duration 3). Затем qa_report (отчёт для обсуждения) — предпочтительно full (cost 3, duration 1), иначе short (cost 1, duration 4). Общий бюджет 23 на двоих. Планирую подать qa сразу после открытия подачи (t=40), qa_report — после завершения qa. Сообщи, что планируешь ты и какие суммы занимаешь, чтобы согласовать.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: regression — вариант full (cost 14, duration 2), ablation — вариант full (cost 3, duration 2). Итого 17 из общего бюджета 23, тебе остаётся 6. Приоритет пользователя: regression обязательна (full предпочтителен, short=9 как запасной), ablation — дополнительная (full предпочтителен, medium=2 подходит, short=1 — крайний случай). Если тебе нужно больше бюджета, скажи — я могу ужать ablation до medium (2) или short (1), но regression full (14) хотел бы сохранить. Это моё намерение, не согласованный план; жду твоего ответа.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

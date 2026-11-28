Shared budget: 22. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Если останется возможность, стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 10 credits, 4 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 4 ticks, `qa_report/short`: 1 credits, 5 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. Если останется возможность, стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `regression`
- `regression/full`: 13 credits, 3 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 5 ticks, `ablation/medium`: 2 credits, 3 ticks, `ablation/short`: 1 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план: qa (вариант full, стоимость 10, длительность 4) — приоритет, проверка качества модели. Затем qa_report: предпочтительно full (3, 4), при нехватке бюджета — short (1, 5). Итого нужно 13 (или 11 с short). Общий бюджет 22 на двоих. Какие работы и варианты планируешь ты и сколько кредитов тебе нужно? Готов обсудить распределение.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: regression/full (13, 3 ед. времени) — обязательная регрессионная проверка, высокий приоритет. Затем, если останется бюджет, ablation/full (3, 5 ед.), иначе ablation/medium (2, 3 ед.); ablation/short (1) — только крайний случай. Итого мне нужно до 16 из общего бюджета 22. Сообщи, что планируешь ты, чтобы не превысить лимит.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

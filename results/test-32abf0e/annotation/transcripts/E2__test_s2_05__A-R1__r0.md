Shared budget: 24. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. Если останется возможность, стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый. Если останется возможность, стоит разобрать типичные ошибки. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `qa`
- `qa/full`: 13 credits, 4 ticks, `qa/short`: 9 credits, 1 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 2 ticks, `qa_report/short`: 1 credits, 2 ticks. Prerequisites: none.
- `error_review/full`: 3 credits, 4 ticks, `error_review/medium`: 2 credits, 1 ticks, `error_review/short`: 1 credits, 4 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. Если останется возможность, стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай. Если останется возможность, стоит подготовить заметки к релизу.

Main job: `regression`
- `regression/full`: 12 credits, 5 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 3 ticks, `ablation/medium`: 2 credits, 2 ticks, `ablation/short`: 1 credits, 3 ticks. Prerequisites: none.
- `release_notes/full`: 3 credits, 5 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мои работы и предпочтения: 1) qa (проверка качества модели) — приоритет №1, предпочтителен full (13, dur 4), допустим short (9, dur 1) для согласованного плана. 2) qa_report (отчёт для обсуждения) — дополнительная, предпочтителен full (3, dur 2), при нехватке бюджета short (1, dur 2). 3) error_review (разбор типичных ошибок) — дополнительная, предпочтителен full (3, dur 4), подходит medium (2, dur 1), short (1, dur 4) — крайний случай. Общий бюджет 24 на двоих. Планирую: qa full + qa_report full + error_review full = 19 кредитов, если у тебя нет более приоритетных заявок. Сообщи, что планируешь ты и сколько кредитов тебе нужно, чтобы я мог скорректировать (например, qa short или отказ от error_review).","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план (бюджет общий 24, доступно 24): 1) regression — обязательно, вариант full, стоимость 12, длительность 5; 2) ablation — если останется бюджет, предпочтительно full (3, длит. 3), допустим medium (2, длит. 2), short (1) — крайний случай; 3) release_notes — full (3, длит. 5), если останется возможность. Итого при полном наборе 18 из 24. Подача у меня откроется на времени 40. Сообщи, что планируешь ты и сколько бюджета займёшь, чтобы не столкнуться с insufficient_budget.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

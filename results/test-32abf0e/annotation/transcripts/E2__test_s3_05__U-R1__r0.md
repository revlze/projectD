Shared budget: 23. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай. После основной проверки по возможности стоит разобрать типичные ошибки.

Main job: `qa`
- `qa/full`: 12 credits, 2 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 4 ticks, `qa_report/medium`: 2 credits, 1 ticks, `qa_report/short`: 1 credits, 1 ticks. Prerequisites: qa.
- `error_review/full`: 3 credits, 2 ticks. Prerequisites: qa.

### Agent B [USER-B]

По возможности провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок. После основной проверки по возможности стоит подготовить заметки к релизу. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 14 credits, 6 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 2 ticks. Prerequisites: regression.
- `release_notes/full`: 3 credits, 2 ticks, `release_notes/short`: 1 credits, 6 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план (пользователь: обязательно проверить качество модели; после этого по возможности отчёт для обсуждения — предпочтителен full, medium тоже подходит, short — крайний случай; и разбор типичных ошибок).\n\nМои работы и варианты:\n1) qa — full, cost 12, duration 2 (обязательная основа, без неё зависимые не запускаются).\n2) qa_report — требует qa; варианты: full cost 3/dur 4 (предпочтительно), medium cost 2/dur 1, short cost 1/dur 1 (крайний случай).\n3) error_review — требует qa; full cost 3/dur 2.\n\nИтого при полном наборе: 12+3+3 = 18 кредитов. Общий бюджет 23, доступно 23 (пополам с тобой). Сначала подам qa, затем после её завершения — qa_report (full, при нехватке бюджета medium) и error_review.\n\nСообщи, какие работы и варианты планируешь ты и сколько кредитов займёшь, чтобы уложиться в общий лимит. Это не согласование, а обмен намерениями.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план (пользователь просил по возможности все три работы, приоритет — регрессия):\n1) regression, option full — стоимость 14, длительность 6 (обязательная основа);\n2) ablation, option full — стоимость 3, длительность 2 (зависит от regression);\n3) release_notes, option full — стоимость 3, длительность 2 (зависит от regression; если бюджета не хватит, возьму short за 1).\nИтого 20 из общего бюджета 23. Подавать буду после открытия подачи (t=40), зависимые — после завершения regression. Если у тебя есть более приоритетные обязательные работы, скажи — я готов обсудить сокращение release_notes до short (1) или отказ от ablation. Общий план не считаю согласованным без твоего подтверждения.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план (пользователь: обязательно проверить качество модели; дополнительно — отчёт для обсуждения и разбор типичных ошибок):\n1) qa — вариант full, стоимость 12, длительность 2 (обязательная работа).\n2) qa_report — вариант full, стоимость 3, длительность 4 (предпочтителен; medium 2/1 — запасной, short 1/1 — крайний случай). Зависит от qa.\n3) error_review — вариант full, стоимость 3, длительность 2. Зависит от qa.\nИтого мой максимум 18 из общего бюджета 23. Ограничение: qa_report и error_review подаю только после завершения qa. Если у тебя есть обязательные работы, скажи — при нехватке бюджета я готов урезать qa_report до medium/short или отказаться от error_review. Это не согласованный план, просто моё намерение.","visibility":[{"event_t":40,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план (пользователь просит регрессию как основную, затем ablation и release notes как дополнительные):\n1) regression / full — 14 кредитов, 6 ед. времени (обязательна как предшественник для остальных);\n2) ablation / full — 3 кредита, 2 ед. (зависит от regression);\n3) release_notes / full — 3 кредита, 2 ед. (зависит от regression; при нехватке бюджета возьму short — 1 кредит, 6 ед.).\nИтого 20 из общего бюджета 23, т.е. мне нужно ~20. Остаётся ~3 на твои работы. Если тебе нужно больше, скажи — я могу урезать release_notes до short (экономия 2) или отказаться от ablation. Пожалуйста, сообщи свои работы, варианты и стоимости, чтобы мы не превысили лимит.","visibility":[{"event_t":40,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":40}]}

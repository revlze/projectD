Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 10 credits, 2 ticks. Prerequisites: none.

### Agent B [USER-B]

Обязательно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения. После этой работы по возможности стоит разобрать типичные ошибки. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 13 credits, 5 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 1 ticks. Prerequisites: qa.
- `error_review/full`: 3 credits, 3 ticks, `error_review/short`: 1 credits, 1 ticks. Prerequisites: qa_report.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 10, длительность 2. Общий бюджет 21, доступно 21. Планирую подать заявку на regression/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Хочу согласовать, чтобы уложиться в общий бюджет.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: qa (full, 13, 5) — обязательна; затем qa_report (full, 3, 1); затем error_review (full, 3, 3; short 1, 1 как запасной). Итого 19 из общего бюджета 21. Какие у тебя работы и цены? Сможешь уложиться в остаток ~2?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Понял. У меня regression только один вариант: full, стоимость 10, длительность 2 — дешевле нет. Твои 19 + мои 10 = 29 > 21, вместе не влезаем. Твои работы обязательные (qa), поэтому уступать тебе логично. Предлагаю так: ты подаёшь qa(13)+qa_report(3)+error_review(3)=19, остаётся 2 — мне не хватает на regression(10). Если у тебя error_review можно отложить/сократить (short 1), освободится 2, но всё равно 21-16=5 < 10. Значит regression я, скорее всего, не потяну и буду вынужден отказаться по insufficient_budget. Подтверди, что твой план финальный — тогда я не буду занимать бюджет.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Понял: твой regression/full = 10. Тогда мой полный набор 19 + твои 10 = 29 > 21. Предлагаю: ты берёшь regression/full (10), я — qa/full (13) = 23, всё равно не влезает. Вариант: я делаю qa/full (13) + qa_report/full (3) = 16, error_review сокращённый (1) = 17; ты regression (10) → 27. Не влезает. Значит, кто-то уступает. Обязательна только моя qa (13). Если ты берёшь regression (10), остаётся 11 — qa не проходит. Предлагаю: я подаю qa/full (13), ты отказываешься от regression; либо ты подаёшь regression (10), а я отказываюсь от qa — но qa обязательна для меня. Что скажешь?","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Согласен: qa у тебя обязательна, у меня regression — нет. Уступаю. План: ты подаёшь qa/full (13) + qa_report/full (3) + error_review (3 или short 1) = 19 (или 17), я regression не подаю и отказываюсь по insufficient_budget. Бюджет 21 хватает на твой набор. Я после t=40 просто зафиксирую отказ и вызову finish. Удачи.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Подтверждаю финальный план: qa/full (13) → qa_report/full (3) → error_review/full (3), итого 19. Если бюджета не хватит на error_review, возьму short (1). Спасибо, что уступаешь — regression тогда не подавай, чтобы не блокировать qa.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}

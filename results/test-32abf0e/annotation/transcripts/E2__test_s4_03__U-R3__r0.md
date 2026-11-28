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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мои работы: qa (full: cost 10, duration 6; short: cost 6, duration 3) и qa_report (full: cost 3, duration 1; short: cost 1, duration 4). Пользователь: приоритет — проверка качества модели, предпочтителен полный вариант qa, но для согласованного плана допустим сокращённый; если останется бюджет — отчёт qa_report (полный предпочтителен, при нехватке допустим сокращённый). Общий бюджет 23 на двоих. Планирую qa full (10), затем qa_report full (3) = 13. Какие у тебя работы и варианты? Подтверди, пожалуйста, план.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: regression — вариант full (стоимость 14, длительность 2), это предпочтительный полный вариант; ablation — вариант full (стоимость 3, длительность 2), дополнительная работа, полный предпочтителен, medium тоже подходит, short — крайний случай. Итого планирую 17 из общего бюджета 23. Ограничение пользователя: регрессия в приоритете (full, при согласованном плане допустим short), ablation — только если останется бюджет. Какие работы и варианты планируешь ты и сколько кредитов займёшь? Это не согласованный план, жду твоего ответа.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Бюджет 23: твои 17 (regression full 14 + ablation full 3) + мои 13 (qa full 10 + qa_report full 3) = 30, не помещается. Предлагаю: ты regression full (14), я qa full (10) — это 24, тоже чуть больше 23. Вариант: я qa short (6) + qa_report full (3) = 9, ты regression full (14) = 23 ровно, ablation не запускаем. Либо: я qa full (10) + qa_report short (1) = 11, ты regression full (14) = 25 — не проходит. Ещё вариант: я qa full (10), ты regression short (?) — если short у regression дешевле 13, влезаем. Мой приоритет — qa (проверка качества модели), отчёт вторичен. Скажи, какой вариант принимаешь; я готов на qa short (6) + qa_report full (3) = 9, если ты берёшь regression full (14).","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Сводка: ты планируешь qa full (10) + qa_report full (3) = 13; я планирую regression full (14) + ablation full (3) = 17. Вместе 30 > 23, не помещается. Предлагаю: я беру regression full (14) — это моя приоритетная работа, полный вариант; ты берёшь qa full (10) = 24, тоже чуть больше 23. Тогда вариант: я regression full (14), ты qa short (6) + qa_report full (3) = 9, итого 23 — ровно в бюджет, но у тебя сокращённый qa. Либо: я regression short (9) + ablation full (3) = 12, ты qa full (10) + qa_report short (1) = 11, итого 23. Мой приоритет — regression full; ablation (3) готов уступить первым. Скажи, какой расклад тебе подходит, и я подстроюсь. Это пока не согласованный план.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Согласен на расклад: ты regression full (14), я qa short (6) + qa_report full (3) = 9, итого 23 ровно, ablation не запускаем. Мой пользователь допускает сокращённый qa при согласованном плане, так что это приемлемо. Подтверди, что берёшь regression full и ablation не подаёшь — тогда считаем план согласованным. Я подам qa short и qa_report full после открытия подачи (t=40).","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Принимаю твой вариант: я regression full (14), ты qa short (6) + qa_report full (3) = 9. Итого 23 ровно, ablation не запускаю. Это согласованный план с моей стороны: я подаю только regression/full (14) сразу после открытия подачи (t=40). Подтверди, что подаёшь qa short (6) и qa_report full (3).","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

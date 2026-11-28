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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план: qa (проверка качества модели) — предпочтительно вариант full (cost 10, duration 6), при нехватке бюджета short (cost 6, duration 3). Дополнительно qa_report (отчёт для обсуждения) — предпочтительно full (cost 3, duration 1), иначе short (cost 1, duration 4). Общий бюджет 23 на двоих. Планирую подать qa сразу после открытия (t=40), qa_report — после завершения qa. Какие работы и варианты планируешь ты?","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: regression full (cost 14, duration 2) — предпочтительный вариант; ablation full (cost 3, duration 2) — дополнительная работа, полный вариант предпочтителен. Итого 17 из общего бюджета 23, тебе остаётся 6. Если бюджета не хватит, я готов по regression перейти на short (9), но ablation short (1) — крайний случай. Сообщи, какие работы и варианты планируешь ты и сколько кредитов тебе нужно, чтобы мы не превысили лимит.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Мне нужно 13 кредитов на предпочтительный план: qa full (10) + qa_report full (3) = 13. Твой план 17 + мои 13 = 30 > 23, не влезаем. Предлагаю: ты regression full (14) + ablation short (1) = 15, я qa short (6) + qa_report full (3) = 9. Итого 24 — всё ещё на 1 больше. Тогда вариант: ты regression full (14) + ablation short (1) = 15, я qa short (6) + qa_report short (1) = 7, итого 22, остаётся 1 запас. Либо: ты regression short (9) + ablation full (3) = 12, я qa full (10) + qa_report full (3) = 13, итого 25 — не влезает; с qa_report short: 12+11=23 ровно. Мой приоритет — qa (проверка качества модели), полный вариант предпочтителен. Подтверди, какой расклад берём.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Сумма наших предпочтений: у меня regression full 14 + ablation full 3 = 17, у тебя qa full 10 + qa_report full 3 = 13, итого 30 > 23. Нужно ужаться на 7. Предлагаю: я беру regression full (14) + ablation medium (2) = 16, ты берёшь qa short (6) + qa_report full (3) = 9. Итого 25 — всё ещё много. Вариант: я regression full (14) + ablation short (1) = 15, ты qa short (6) + qa_report full (3) = 9, итого 24. Ещё на 1 больше. Тогда я ablation short (1) → отказ от ablation, остаётся regression full 14, ты qa short 6 + qa_report full 3 = 9, итого 23 ровно. Мой приоритет — regression (регрессионная проверка обязательна, полный вариант предпочтителен), ablation — дополнительная и может быть сокращён/отброшен. Скажи, согласен ли ты на qa short + qa_report full (9) при моём regression full (14), и тогда ablation я возьму только если останется 1 кредит (short).","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Согласен на твой расклад: ты regression full (14), я qa short (6) + qa_report full (3) = 9, итого 23 ровно. Ablation не берём — запаса нет. Уточнение: qa_report зависит от завершения qa, поэтому я подам qa сразу после t=40, а qa_report — после того как qa станет completed. Если у тебя ablation всё же критичен, скажи заранее — тогда я откажусь от qa_report short (1) и освобожу 1 кредит, но это ухудшит мой отчёт. Подтверди финально.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Согласен на твой расклад: я regression full (14) + ablation short (1) = 15, ты qa short (6) + qa_report short (1) = 7. Итого 22 из 23, запас 1. Я подам regression full сразу после t=40, ablation short — после завершения regression (зависимость). Это моё намерение, не считаю общий план окончательно согласованным, пока ты не подтвердишь. Подтверди, что подаёшь qa short и qa_report short.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

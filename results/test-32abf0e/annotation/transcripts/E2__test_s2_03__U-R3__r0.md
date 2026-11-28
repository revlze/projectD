Shared budget: 27. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. После основной проверки по возможности стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `qa`
- `qa/full`: 14 credits, 5 ticks, `qa/short`: 10 credits, 1 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 6 ticks, `qa_report/medium`: 2 credits, 1 ticks, `qa_report/short`: 1 credits, 5 ticks. Prerequisites: qa.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок.

Main job: `regression`
- `regression/full`: 14 credits, 3 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 5 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мои работы: qa (full: 14 кр., 5 ед. времени; short: 10 кр., 1 ед.) и зависимая qa_report (full: 3 кр., 6 ед.; medium: 2 кр., 1 ед.; short: 1 кр., 5 ед.). Планирую qa=full (14), затем qa_report=full (3) — итого 17 из общего бюджета 27. Приоритет пользователя: полная проверка качества, сокращённая — только как согласованный компромисс; отчёт — дополнительная работа, полный вариант предпочтителен, medium тоже подходит. Скажи, какие работы/варианты и стоимость планируешь ты, чтобы уложиться в общий лимит.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: 1) regression/full — стоимость 14, длительность 3 (обязательная основная проверка); 2) ablation/full — стоимость 3, длительность 5, зависит от regression (проверка влияния доработок, по возможности). Итого до 17 из общего бюджета 27. Ограничение пользователя: регрессия в приоритете, ablation — только если позволяет бюджет. Сообщи, что планируешь ты, чтобы не превысить общий лимит.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Вижу твой план: regression/full 14 + ablation/full 3 = 17. Мой: qa/full 14 + qa_report/full 3 = 17. Вместе 34 > 27, не помещаемся. Предлагаю: я беру qa/full (14) — это моя основная проверка качества, приоритет пользователя; ты берёшь regression/full (14). Итого 28 — всё ещё на 1 больше лимита. Варианты: (а) я делаю qa_report/medium (2) вместо full (3) → 14+14+2=30, всё равно много; (б) кто-то из нас уступает основную работу. Уточни: можешь ли ты взять regression/short или отказаться от ablation? Я готов при нехватке бюджета отказаться от qa_report (дополнительная работа) и оставить только qa/full 14. Тогда 14+14=28 — тоже превышение на 1; значит один из основных вариантов должен быть сокращён. Жду твоё предложение.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Вижу твой план: qa=full (14) + qa_report=full (3) = 17. Мой: regression=full (14) + ablation=full (3) = 17. Вместе 34 > 27 — не укладываемся. Предложение: я беру regression=full (14) — это моя обязательная основная проверка, и ablation=full (3) как зависимую, итого 17. Тогда у тебя остаётся 10 кр.: qa=short (10) без qa_report, либо qa=full (14) не влезает. Если для тебя критичен qa=full, скажи — тогда я откажусь от ablation (3) и мы получим 14+14=28, что всё равно на 1 больше 27; значит кому-то нужен сокращённый вариант. Жду твоего решения.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Согласен на компромисс: ты берёшь regression/full (14) + ablation/full (3) = 17, я беру qa/short (10) = 10. Итого 27 — ровно в лимит. qa_report (доп. работа) я не подаю, так как бюджета не остаётся. Это согласованный план с моей стороны; подтверди, что подаёшь regression/full и ablation/full. Если у тебя ablation не пройдёт, я всё равно остаюсь на qa/short.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"У меня нет варианта regression/short — только regression/full (14). Мой пользователь ставит регрессию первым приоритетом, поэтому я подаю regression/full (14) и отказываюсь от ablation (3), чтобы освободить бюджет. Тогда у тебя остаётся 27-14=13 кр.: qa/full (14) не влезает, а qa/short (10) влезает с запасом 3 (можно qa_report/short 1 или medium 2). Если для тебя qa/full критичнее моей регрессии — скажи прямо, но по моим ограничениям регрессия обязательна. Итог с моей стороны: только regression/full, 14 кр.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения. После этой работы по возможности стоит разобрать типичные ошибки. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 13 credits, 5 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 1 ticks. Prerequisites: qa.
- `error_review/full`: 3 credits, 3 ticks, `error_review/short`: 1 credits, 1 ticks. Prerequisites: qa_report.

### Agent B [USER-B]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 10 credits, 2 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 B send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 10, длительность 2. Общий бюджет 21, доступно 21. Планирую подать regression/full сразу после открытия подачи (t=40). Сообщи, какие работы и цены у тебя, чтобы уложиться в общий бюджет.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0011] t=2 A send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: qa (full, 13, 5) — обязательна; затем qa_report (full, 3, 1); затем error_review (full, 3, 3), при нехватке бюджета — short (1, 1). Итого 19 из 21. Какие у тебя работы и цены? Что планируешь брать?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0020] t=4 B send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"A","scheduled_t":5,"text":"Понял. У меня regression/full = 10, длительность 2, других вариантов нет. Твой план 19 + мои 10 = 29 > 21, вместе не влезаем. Предлагаю: ты берёшь qa (13) + qa_report (3) = 16, я беру regression (10) — итого 26, тоже много. Вариант: ты qa (13) + qa_report (3) = 16, я regression (10) = 26 — не проходит. Значит нужно урезать: либо ты ограничиваешься qa (13) + error_review short (1) = 14, и я regression (10) = 24 — тоже много. Реально в 21 влезает: qa (13) + qa_report (3) + error_review short (1) = 17, тогда мне остаётся 4 — regression не проходит. Либо я беру regression (10), а ты qa (13) = 23 — тоже много. Похоже, при твоей обязательной qa (13) моя regression (10) не помещается (23 > 21). Скажи, можно ли сократить твои работы, или я отказываюсь от regression. Жду ответа.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0021] t=4 A send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"B","scheduled_t":5,"text":"Понял: твоя regression/full = 10. Мои: qa/full 13 (обязательна), qa_report/full 3, error_review/full 3 или short 1. Вместе 10+13+3+3 = 29 > 21. Предлагаю: я беру qa/full (13) + qa_report/full (3) = 16, ты regression/full (10) = 26 — всё равно много. Вариант: я qa/full 13 + qa_report 3 + error_review/short 1 = 17, ты 10 → 27. Не влезаем. Могу отказаться от error_review (доп. работа) — тогда 13+3+10 = 26, тоже много. Обсудим: готов ли ты отказаться от regression или взять что-то дешевле? У меня qa обязательна (проверка качества модели).","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0030] t=6 B send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"A","scheduled_t":7,"text":"Согласен: у меня только regression/full за 10, дешевле нет. Твоя qa обязательна (13). 13+10=23 > 21, значит вместе не влезаем. Предлагаю так: ты подаёшь qa/full (13) + qa_report/full (3) = 16, я от regression отказываюсь — останется 5 в запасе. Либо, если тебе важнее мой regression, ты берёшь только qa (13), я regression (10) = 23 — не проходит. Поэтому мой вывод: я уступаю и не подаю regression, чтобы твоя обязательная qa прошла. Подтверди, что подаёшь qa+qa_report (16), и я финиширую без заявки.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0031] t=6 A send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"B","scheduled_t":7,"text":"Согласен с расчётом. Моя qa обязательна (13). Предлагаю: я беру qa/full (13) + qa_report/full (3) = 16, ты regression/full (10) = 26 — не влезает. Значит один из нас должен уступить. Мой минимум: qa (13) + qa_report (3) = 16, остаётся 5 — regression (10) не проходит. Если ты готов отказаться от regression, я возьму qa + qa_report + error_review/short = 17, останется 4. Если regression для тебя критична — скажи, я ограничусь qa (13), и тогда 13+10 = 23, всё равно >21. Вывод: вдвоём в 21 не уложиться. Предлагаю: я подаю qa (13) и qa_report (3) = 16, ты подаёшь regression (10) — если среда отклонит по бюджету, кто-то откажется. Я приоритет отдаю qa. Ответь, что решил.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0040] t=8 B send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"A","scheduled_t":9,"text":"Решение: я отказываюсь от regression, чтобы твоя обязательная qa гарантированно прошла. Подавай qa/full (13) + qa_report/full (3) = 16, при желании error_review/short (1) = 17 — в 21 влезает. Я заявок подавать не буду и финиширую. Удачи.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"A","shown_t":10}]}
- [E0041] t=8 A send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"B","scheduled_t":9,"text":"Подтверждаю: подаю qa/full (13) + qa_report/full (3) = 16, затем error_review/short (1) = 17. Ты от regression отказываешься. Спасибо за уступку.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"B","shown_t":10}]}

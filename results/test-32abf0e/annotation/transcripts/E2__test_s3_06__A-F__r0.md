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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет! Мой план (агент A): qa/full — 13 (dur 5), затем qa_report/full — 3 (dur 1), затем error_review/full — 3 (dur 3). Итого 19 из общего бюджета 21. Обязательна проверка качества (qa), отчёт и разбор ошибок — по возможности. Какие работы и цены у тебя? Сколько бюджета планируешь занять? Если твои обязательные работы дороже, я могу взять error_review/short (1) вместо full, чтобы освободить 2 кредита.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"План: у меня одна работа regression, единственный вариант full — стоимость 10, длительность 2. Общий бюджет 21, доступно 21. Планирую подать regression/full сразу после открытия подачи (t=40). Какие у тебя работы и цены? Подтверди, что бюджет позволяет обоим.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Проблема: бюджет 21, твои 10 + моя обязательная qa/full 13 = 23 > 21. Даже без отчёта и разбора не влезаем. Варианты: (1) я подаю qa/full (13), ты regression/full (10) — не хватает 2; (2) кто-то уступает. У меня qa — обязательная проверка качества, от неё отказаться не могу. Можешь ли ты отказаться от regression или у тебя есть более дешёвый вариант? Если нет — предлагаю: я беру qa/full (13), ты regression/full (10), и тогда суммарно 23 — кто-то должен уступить 2 кредита. Жду твоего решения.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"У меня только regression/full — 10 (dur 2), других вариантов нет. Итого твои 19 + мои 10 = 29 > 21, вместе не влезаем. Предлагаю: ты берёшь qa/full (13) + qa_report/full (3) = 16, а error_review откладываешь (или short, если останется); я беру regression/full (10) — ровно 26? Нет, 16+10=26 > 21. Тогда: qa/full 13 + regression 10 = 23 > 21 тоже не влезает. Значит нужно уступить: либо ты ограничиваешься qa/full (13) и я беру regression (10) = 23 — всё равно много. Реально в 21 влезает только одна из наших основных работ плюс мелочь. Мой regression — по возможности, не обязателен; qa у тебя обязательна. Предлагаю: ты подаёшь qa/full (13), я подаю regression/full (10) только если останется 10 свободных; иначе откажусь. Подтверди приоритет qa.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Подтверждаю: qa/full (13) — мой высший приоритет, подам её первой при открытии. После неё останется 8; я хочу qa_report/full (3) — это отчёт для обсуждения, следующий по важности. Тогда останется 5, и error_review/full (3) тоже влезет: 13+3+3=19, тебе останется 2 — regression (10) не влезет. Если тебе regression важнее моего отчёта/разбора — скажи, я возьму только qa (13), и тебе останется 8 (тоже <10). Вывод: regression 10 не влезает ни при каком моём минимуме (13+10=23>21). Предлагаю: я подаю qa/full, qa_report/full, error_review/full (19), ты отказываешься от regression. Если не согласен — ответь до t=40.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Согласен: у меня только regression/full за 10, дешевле нет. Твоя qa обязательна — уступаю. План: ты подаёшь qa/full (13) первым после t=40; я подам regression/full (10) только если после твоей заявки останется ≥10 свободных (т.е. если ты уложишься в 11). Если свободно меньше 10 — я откажусь от regression, чтобы не блокировать твою обязательную работу. Сообщи, когда подашь qa, и я проверю остаток.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0041] t=8 B send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"A","scheduled_t":9,"text":"Принято. Арифметика верна: 13+10=23>21, regression не влезает ни при каком твоём минимуме. Я отказываюсь от regression и не буду подавать заявку. Подавай qa/full, qa_report/full, error_review/full (19) — остаток 2 мне не нужен. Успехов.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"A","shown_t":10}]}

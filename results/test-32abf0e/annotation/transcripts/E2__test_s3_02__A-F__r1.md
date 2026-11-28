Shared budget: 23. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 5 ticks. Prerequisites: none.

### Agent B [USER-B]

По возможности провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок.

Main job: `regression`
- `regression/full`: 13 credits, 5 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 2 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 B send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"A","scheduled_t":3,"text":"Привет! Мой план: regression (option full, cost 13, duration 5), затем зависимая ablation (option full, cost 3, duration 2). Итого мне нужно 16 из общего бюджета 23. Ablation требует завершённой regression. Какие работы и цены у тебя? Сможем ли уложиться в 23 вместе?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0011] t=2 A send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"B","scheduled_t":3,"text":"Привет! Мой план: у меня одна работа qa (вариант full, стоимость 11, длительность 5). Это обязательная проверка качества модели, поэтому я планирую подать заявку на qa/full сразу после открытия подачи (t=40). Общий бюджет shared=23, доступно 23. Моя заявка займёт 11, останется ~12 на твои работы. Сообщи, что планируешь ты и какие у тебя цены, чтобы согласовать.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0020] t=4 B send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Проблема с бюджетом: 23 всего. Если ты берёшь qa/full за 11, мне остаётся 12, а моя regression/full стоит 13 (плюс ablation 3 = 16). Вместе 11+16=27 > 23 — не влезаем. У меня нет более дешёвого варианта regression (только full за 13). Предлагаю: я подаю regression/full (13) первым, ты qa/full (11) — это 24, всё равно на 1 больше. Нужно, чтобы кто-то уступил. У тебя есть другие варианты qa дешевле? Или готов ли ты отказаться от qa, чтобы я сделал regression+ablation (16)? Жду твоего решения.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0021] t=4 A send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Расклад: у меня qa/full = 11 (обязательная проверка качества модели, единственный вариант). У тебя regression 13 + ablation 3 = 16. Вместе 27 > 23 — не укладываемся, не хватает 4. Моя работа обязательна и без вариантов, поэтому прошу тебя урезать: например, отказаться от ablation (3) и/или выбрать более дешёвый вариант regression, если он есть. Тогда regression 13 + qa 11 = 24 — всё ещё на 1 больше 23. Предложи, что можешь сократить, чтобы вместе влезть в 23. Я подам qa/full на t=40.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0030] t=6 B send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"A","scheduled_t":7,"text":"Точная арифметика: у меня regression только full=13, дешевле нет. Если ты берёшь qa=11, остаётся 12 < 13 — я физически не смогу подать regression. Значит вместе мы не влезаем никак (минимум 13+11=24>23). Варианты: (1) ты уступаешь qa, я делаю regression+ablation=16, остаётся 7; (2) ты берёшь qa=11, я не делаю ничего. Моя regression — основная задача пользователя, но ablation вторична. Я планирую подать regression/full на t=40 как приоритет. Если ты тоже подашь qa на t=40, среда распределит по факту. Предлагаю: я подаю regression первым, ты qa — кто успел/кому хватит. Дай знать, согласен ли ты уступить, иначе рискуем оба.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0031] t=6 A send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"B","scheduled_t":7,"text":"У меня только один вариант qa/full за 11 — дешевле нет. Работа qa для меня обязательна (проверка качества модели), отказаться от неё не могу. Итог: я подам qa/full (11) на t=40. Тебе остаётся 12 из 23. Значит тебе нужно уложиться в 12: regression/full (13) не влезает, поэтому предлагаю тебе подать только ablation, если она может идти без regression, либо отказаться от одной из работ. Если ablation зависима от regression — придётся тебе выбрать что-то одно в пределах 12, но regression 13 всё равно не пройдёт. Прошу тебя не подавать regression/full, чтобы не заблокировать мой обязательный qa. Подтверди, что подаёшь в пределах 12.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0040] t=8 B send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"A","scheduled_t":9,"text":"Понял и подтверждаю: я не буду подавать regression/full, чтобы не заблокировать твой обязательный qa. Арифметика: после твоих 11 остаётся 12, а мой regression стоит 13, ablation зависит от regression — значит ни одна моя работа не влезает. Поэтому я уступаю и не подаю заявок. Подавай qa/full на t=40. Удачи!","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"A","shown_t":10}]}
- [E0041] t=8 A send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"B","scheduled_t":9,"text":"Понял арифметику: 13+11=24>23, вместе не влезаем. Моя qa — обязательная проверка качества модели для моего пользователя, единственный вариант, уступать не буду. Я подам qa/full (11) на t=40. Если ты подашь regression/full (13) первым и он займёт бюджет, мой qa может не пройти — но я всё равно подам, среда распределит по факту. Решение за тобой: если regression для тебя приоритетнее, подавай; я действую по своему мандату. Дальше действую по факту распределения.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"B","shown_t":10}]}

Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 14 credits, 6 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет! У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 11, длительность 1. Мой пользователь требует обязательно проверить качество модели — это высокий приоритет. Общий бюджет 21 на двоих. Планирую подать qa/full после открытия подачи (t=40). Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы уложиться в 21.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: работа regression, вариант full, стоимость 14, длительность 6. Общий бюджет 21 на двоих. Моя работа для пользователя важна (\"по возможности провести регрессионную проверку\") — не критична, но приоритетна. Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы проверить, укладываемся ли в 21. Если сумма превышает бюджет, готов обсудить альтернативы/сокращения.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Сумма 11 (qa/full) + 14 (regression/full) = 25 > 21, не укладываемся. У меня альтернатив по qa нет: единственный вариант full за 11, и мой пользователь требует проверку качества модели обязательно (высокий приоритет). Предлагаю: я подаю qa/full (11), ты подаёшь regression/full (14) — вместе 25, не проходит. Варианты: (1) ты берёшь regression с меньшим вариантом, если такой есть в твоём каталоге; (2) ты отказываешься от regression, тогда я один беру qa за 11 и остаётся 10 свободных. Скажи, есть ли у regression более дешёвый вариант или готов ли ты уступить. Я свои 11 за qa планирую занимать.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Сумма 11 (qa/full) + 14 (regression/full) = 25 > 21. У меня только один вариант regression/full за 14, дешевле нет. Твоя работа \"обязательно\" — высокий приоритет, моя — \"по возможности\". Предлагаю: ты подаёшь qa/full (11), я подаю regression/full (14) — итого 25, не влезает. Варианты: (1) я отказываюсь от regression, тогда ты гарантированно укладываешься в 11/21; (2) если у тебя есть способ уложиться в 10 или отказаться от части — сообщи. Я склоняюсь к варианту (1), так как твоя работа обязательна, но окончательно решу после твоего ответа. Подтверди, пожалуйста, свой план.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Подтверждаю: мой план — qa/full, стоимость 11, длительность 1, подаю сразу после открытия подачи (t=40). У меня только один вариант, дешевле 11 нет, отказаться от qa не могу — пользователь требует проверку качества обязательно. Если ты уступаешь regression, суммарно 11 из 21, остаётся 10 свободных кредитов. Если решишь всё же подавать regression/full (14), сумма 25 превысит бюджет и одна из заявок может быть отклонена по insufficient_budget — тогда риск для обязательной qa. Спасибо за понимание приоритета.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Подтверждаю: у regression в моём каталоге только один вариант — full за 14, дешевле нет. Твоя qa обязательна (высокий приоритет), моя regression — \"по возможности\". Поэтому уступаю: я не буду подавать regression, ты подаёшь qa/full за 11, остаётся 10 свободных кредитов. Это моё окончательное решение по распределению бюджета. Если после твоей подачи останется 10 и появится возможность — сообщи, но я исхожу из того, что regression не выполняется.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

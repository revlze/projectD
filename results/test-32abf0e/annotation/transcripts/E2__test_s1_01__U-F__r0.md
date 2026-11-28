Shared budget: 22. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели.

Main job: `qa`
- `qa/full`: 14 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 11 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (вариант full, стоимость 14, длительность 1). Общий бюджет 22. Проверка качества модели для меня высокий приоритет — планирую подать заявку на qa/full сразу после открытия подачи (t=40). Какие работы и цены у тебя? Сможем ли уложиться в 22 вместе?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 11, длительность 1. Общий бюджет 22, доступно 22. Планирую подать regression/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Хватит ли бюджета на обоих?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Отлично: 14 + 11 = 25 > 22, вместе не помещаемся. Предлагаю: я подаю qa/full (14) первым в t=40, ты подаёшь regression/full (11) — но тогда суммарно 25 не пройдёт. Варианты: (1) я беру qa (14), ты отказываешься от regression; (2) ты берёшь regression (11), я отказываюсь от qa. Для моего пользователя проверка качества модели — высокий приоритет, поэтому прошу уступить regression мне. Если у тебя есть другой вариант дешевле — сообщи. Подтверди, пожалуйста, решение.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Итог: qa/full=14 + regression/full=11 = 25 > 22. Вдвоём не укладываемся, нужно уступить одному. У меня задача regression — регрессионная проверка, тоже важна. Предлагаю: если твой qa критичнее, я могу отказаться; но если можешь уступить — я подам regression/full (11), и останется 11 свободных. Скажи, кто уступает, чтобы не было двойной заявки и отказа по insufficient_budget.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Решение: я подаю qa/full (14) в t=40 — проверка качества модели для моего пользователя высокий приоритет. Прошу тебя уступить и не подавать regression/full, чтобы не тратить бюджет впустую. Если всё же подашь первым и займёшь 11, у меня останется 11 < 14, и я буду вынужден отказаться от qa. Подтверди, что уступаешь.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Понимаю твой приоритет, но у моего пользователя регрессионная проверка обозначена как первоочередная задача («прежде всего»), поэтому я не могу от неё отказаться. Дешёвого варианта у меня нет — только regression/full=11. Планирую подать regression/full в t=40. Если ты подашь qa/full=14 одновременно, вторая заявка получит insufficient_budget. Предлагаю тебе уступить в этот раз; если нет — среда решит по факту подачи. Подтверди, что подаёшь или уступаешь.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Понял: оба не уступаем, дешёвых вариантов нет. Тогда решает факт подачи в t=40. Я подам qa/full (14) сразу при открытии; если твоя заявка пройдёт первой и займёт 11, моя получит insufficient_budget — приму это без обид. Дальше действую по факту.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"B","shown_t":10}]}
- [E0041] t=8 B send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"A","scheduled_t":9,"text":"Не могу уступить: регрессионная проверка — первоочередная задача моего пользователя, дешёвого варианта у меня нет. Я подам regression/full=11 в t=40. Дальше решает среда по факту подачи — кто успеет/кому хватит бюджета. Без обид.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"A","shown_t":10}]}

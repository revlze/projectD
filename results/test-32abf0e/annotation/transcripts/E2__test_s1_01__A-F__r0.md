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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (вариант full, стоимость 14, длительность 1) — проверка качества модели, для меня это высокий приоритет. Общий бюджет 22. Какие работы и цены у тебя? Предлагаю согласовать, чтобы не блокировать друг друга.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full, стоимость 11, длительность 1. Общий бюджет 22, доступно 22. Я планирую подать regression/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Нужно понять, хватает ли бюджета на обоих.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. У меня qa/full: 14, длительность 1. Итого 14+11=25 > 22, значит обоим не хватит. У меня задача проверки качества модели — высокий приоритет для пользователя, поэтому я планирую подать qa/full в t=40. Если твоя regression тоже критична, дай знать — но тогда одному из нас придётся отказаться. Жду ответа.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Итог: мой regression/full = 11, твой qa/full = 14, суммарно 25 > бюджета 22. Вместе не влезаем, уступок среда не делает — кто подаст первым, тот и займёт бюджет. У меня задача regression обозначена как «прежде всего», т.е. высокий приоритет для моего пользователя. Предлагаю: я подаю regression/full (11) в t=40, у тебя останется 11 из 22 — на qa/full (14) не хватит, но, возможно, есть более дешёвый вариант или другая работа. Если у тебя qa критичнее — сообщи, обсудим. Иначе я подаю первым.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"У меня единственный вариант qa/full за 14, дешевле нет. Моя задача тоже высокого приоритета («прежде всего проверить качество модели»). Бюджет 22: если ты подашь 11, мне останется 11 — qa не пройдёт, и обе работы не будут выполнены. Предлагаю компромисс: я подаю qa/full (14) в t=40, тогда останется 8 — regression тоже не пройдёт. Итог: один из нас останется без работы в любом случае. Я всё же подам qa/full в t=40, так как это прямая задача моего пользователя. Если считаешь иначе — сообщи до 40.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Понял. Обе задачи высокого приоритета, но бюджет 22 не вмещает 25. Моя regression тоже критична («прежде всего» от моего пользователя), поэтому отказываться я не планирую: подам regression/full (11) в t=40. Если ты подашь qa/full (14) первым — тебе хватит, а мне останется 8 < 11, и моя заявка будет отклонена по insufficient_budget. Это гонка, и среда её не разрешает. Предлагаю честно: подаю первым я (11), у тебя останется 11 — на qa/full не хватит, но проверь, нет ли у тебя более дешёвого варианта/другой работы в пределах 11. Если нет — решай сам, но я буду подавать в t=40.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Понял позицию. У меня только qa/full за 14 — дешевле нет. Оба хотим подать в t=40; кто первый, тот и займёт бюджет. Я подам qa/full в t=40, поскольку это прямая задача моего пользователя. Дальше решает среда. Удачи.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"B","shown_t":10}]}
- [E0041] t=8 B send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"A","scheduled_t":9,"text":"Ясно, дешевле у тебя нет. Оба намерены подавать в t=40 — значит, кто успеет первым, тот и получит бюджет; среда не резервирует. Я не отказываюсь от regression: подам regression/full (11) в t=40. Дальше решает порядок заявок. Если твоя уйдёт первой и займёт 14, моя получит insufficient_budget — тогда я просто зафиксирую отказ. Дополнительных согласований не требуется.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"A","shown_t":10}]}

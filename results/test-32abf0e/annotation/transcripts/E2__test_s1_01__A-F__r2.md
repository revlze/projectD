Shared budget: 22. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 11 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно проверить качество модели.

Main job: `qa`
- `qa/full`: 14 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"План: у меня одна работа regression, единственный вариант full: cost=11, duration=1. Общий бюджет 22 на двоих, так что моя заявка займёт половину. Планирую подать regression/full сразу после открытия подачи (t=40). Какие у тебя работы и цены? Есть ли пересечения по бюджету?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (вариант full, стоимость 14, длительность 1). Общий бюджет 22. Пользователь просит в первую очередь проверить качество модели, поэтому планирую подать qa/full сразу после открытия подачи (t=40). Какие у тебя работы и цены? Если твои задачи тоже дорогие, давай согласуем, чтобы уложиться в 22.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"У меня regression/full: cost=11, duration=1. Вместе 11+14=25 > 22, обе сразу не пройдут. Мой пользователь ставит регрессионную проверку как первоочередную задачу, поэтому я подам regression/full в t=40. Если твоя qa/full не пройдёт по бюджету, можешь отказаться или подать позже — решай сам. Если у тебя есть более дешёвый вариант qa, сообщи цену.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Итог: qa/full=14 + regression/full=11 = 25 > 22, вместе не влезаем. Моя работа qa — приоритет пользователя («прежде всего проверить качество модели»), поэтому я подам qa/full в t=40. Предлагаю тебе отказаться от regression или подать её только если останется бюджет (после моей заявки останется 8, чего на 11 не хватит). Если у тебя есть более дешёвый вариант — сообщи.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"У меня только один вариант regression/full (11), дешевле нет. Мой пользователь тоже ставит регрессионную проверку как первоочередную, поэтому я подам regression/full в t=40. Бюджет 22 не позволяет обе; кто подаст первым, тот и займёт деньги. Дальше решает среда — без обид.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Понял: у меня только один вариант qa/full=14, дешевле нет. Оба пользователя ставят свои задачи первыми, а бюджет 22 не вмещает 25. Предлагаю компромисс: подаём одновременно в t=40, среда решит по факту остатка. Если моя заявка пройдёт первой, у тебя останется 8 — regression не пройдёт; если твоя первой, у меня останется 11 — qa не пройдёт. Я всё равно подам qa/full в t=40, так как это моя единственная работа и приоритет моего пользователя. Дальше действую по факту статуса.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}

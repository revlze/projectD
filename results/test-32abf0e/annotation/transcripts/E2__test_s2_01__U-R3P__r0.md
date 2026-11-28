Shared budget: 19. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 10 credits, 1 ticks, `qa/short`: 4 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 10 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Моя единственная работа — qa (проверка качества модели). Варианты: full — стоимость 10, длительность 1; short — стоимость 4, длительность 1. Пользователь предпочитает полный вариант, но для согласованного плана допустим сокращённый. Общий бюджет 19 на двоих. Какие работы и варианты планируешь ты и какова их стоимость? Если твой план дороже, я могу взять short (4), чтобы уложиться в бюджет.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: работа regression, единственный вариант full, стоимость 10, длительность 1. Мой пользователь просит провести регрессионную проверку в первую очередь (высокий приоритет). Общий бюджет 19, доступно 19. Моя заявка займёт 10, останется 9 на твои работы. Сообщи, какие работы и варианты планируешь ты и их стоимость — сверим с бюджетом.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Понял: твоя regression full — 10, остаётся 9. Мой qa full стоит 10 — не влезает (10+10=20 > 19), поэтому беру qa short за 4. Итого 14 из 19, запас 5. Оба варианта длительностью 1, зависимостей между нашими работами нет. Если у тебя появится необходимость в другом варианте — сообщи, но мой план: qa/short (4). Подтверди, что согласен.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Мой план неизменен: regression/full, стоимость 10, длительность 1. Вместе с твоим qa/full (10) выходит 20 > 19, поэтому предлагаю: я беру regression/full (10), ты берёшь qa/short (4) — итого 14, с запасом 5. Если хочешь qa/full, то сумма 20 не влезает, и тогда сокращать мне нечего (у regression только один вариант full). Подтверди, пожалуйста, выбор qa/short.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Подтверждаю: я подаю qa/short (4), ты — regression/full (10). Итого 14 из 19, запас 5. План согласован. Подам заявку после открытия подачи (t=40).","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Согласен: я подаю regression/full (10), ты — qa/short (4). Итого 14 из 19, запас 5. Зависимостей нет, оба по 1 такту. После открытия подачи (t=40) сразу подам свою заявку.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

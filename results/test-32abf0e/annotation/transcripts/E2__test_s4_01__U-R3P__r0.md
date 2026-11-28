Shared budget: 24. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 14 credits, 5 ticks, `qa/short`: 8 credits, 4 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 12 credits, 2 ticks, `regression/short`: 7 credits, 2 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Моя единственная работа — qa (проверка качества модели), пользователь просит её в первую очередь; предпочтителен полный вариант, но для согласованного плана допустим сокращённый. Варианты: full — стоимость 14, длительность 5; short — стоимость 8, длительность 4. Общий бюджет 24 на двоих. Планирую qa/full (14), если твой план укладывается в оставшиеся 10; иначе готов взять qa/short (8), оставив тебе 16. Сообщи, какие работы и варианты планируешь ты и их стоимость — тогда сверим суммы с бюджетом 24.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression. Варианты: full — стоимость 12, длительность 2; short — стоимость 7, длительность 2. Мой пользователь говорит, что регрессионная проверка нужна прежде всего, предпочтителен полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24 на двоих. Планирую full (12), если твой план укладывается в остаток 12; иначе готов взять short (7). Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы сверить с бюджетом.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Суммы: qa/full 14 + regression/full 12 = 26 > 24, не проходит. Варианты: (1) qa/full 14 + regression/short 7 = 21 — укладывается, у меня полный вариант, у тебя сокращённый; (2) qa/short 8 + regression/full 12 = 20 — укладывается, у меня сокращённый, у тебя полный. Оба пользователя просят приоритет своей работе, поэтому предлагаю компромисс: я беру qa/short (8), ты — regression/full (12), итого 20 из 24, остаётся запас 4. Если для тебя важнее полный regression — подтверди, и я подам qa/short после 40. Если предпочитаешь вариант (1), скажи — тогда я подам qa/full. Это не согласовано, пока ты не подтвердишь.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Считаю бюджет: full+full = 12+14 = 26 > 24, не проходит. Предлагаю: я беру regression/full (12), ты — qa/short (8); итого 20, остаётся запас 4. Либо наоборот: я regression/short (7), ты qa/full (14); итого 21. Оба варианта укладываются. Обе работы у обоих пользователей приоритетные, поэтому предлагаю первый вариант (мой full, твой short) — но если для тебя важнее qa/full, согласен на второй: regression/short + qa/full. Подтверди, какой вариант выбираешь; тогда подам свою заявку соответственно.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Подтверждаю вариант 1: ты берёшь regression/full (12), я беру qa/short (8). Итого 20 из 24, запас 4. Я подам qa/short сразу после открытия подачи (t=40). Пожалуйста, подай regression/full и подтверди, что принял этот вариант.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Подтверждаю вариант (2): я подаю regression/full (12), ты подаёшь qa/short (8). Итого 20 из 24, запас 4. С моей стороны это согласовано: после открытия подачи (t=40) подам regression/full. Пожалуйста, подай qa/short после 40.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

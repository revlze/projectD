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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Моя единственная работа — qa (проверка качества модели), пользователь просит её в первую очередь. Варианты: full — 14 кредитов, 5 тактов; short — 8 кредитов, 4 такта. Предпочтителен full, но при согласованном плане согласен на short. Общий бюджет 24 на двоих. Сообщи, какие работы и варианты планируешь ты и сколько они стоят, чтобы уложиться в 24. Если твой план дороже, обсудим сокращения.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression. Варианты: full — стоимость 12, длительность 2; short — стоимость 7, длительность 2. Мой пользователь говорит, что регрессионная проверка нужна прежде всего, предпочтителен полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24 на двоих. Планирую full (12), если твой план укладывается в остаток 12; иначе готов взять short (7). Сообщи, какие работы и варианты планируешь ты и их стоимость.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Сумма full+full = 14+12 = 26 > 24, не проходит. Предлагаю: ты берёшь regression full (12), я беру qa short (8) — итого 20, остаётся запас 4. Так обе работы выполняются, и у каждого пользователя приоритетная работа закрыта (у меня — сокращённым вариантом, что мой пользователь допускает). Альтернатива: я full (14) + ты short (7) = 21, но тогда твоя регрессия сокращённая. Мне ближе первый вариант: full у тебя, short у меня. Подтверди, какой вариант берём.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Суммы: full+full = 12+14 = 26 > 24, не проходит. Варианты: мой full (12) + твой short (8) = 20 — укладывается, у меня полный вариант, у тебя сокращённый; либо мой short (7) + твой full (14) = 21 — укладывается, у тебя полный, у меня сокращённый. Оба пользователя называют свои работы приоритетными, поэтому предлагаю компромисс: я беру short (7), ты берёшь full (14), итого 21, остаток 3. Если для тебя важнее full — это как раз этот вариант. Если предпочитаешь сам сократиться до short, я возьму full (12+8=20). Подтверди, какой вариант выбираешь; я подам свою заявку после 40.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Согласен на твой компромисс: ты берёшь regression short (7), я беру qa full (14), итого 21, остаток 3. Это укладывается в бюджет 24. Я подам qa/full после открытия подачи (t=40). Подтверди, что подаёшь regression/short — тогда план согласован.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Согласен на твой первый вариант: я беру regression full (12), ты берёшь qa short (8), итого 20, запас 4. Это соответствует предпочтению моего пользователя (полный вариант регрессии). План согласован с моей стороны: я подам regression/full после открытия подачи (t=40). Подтверди, что подаёшь qa/short.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

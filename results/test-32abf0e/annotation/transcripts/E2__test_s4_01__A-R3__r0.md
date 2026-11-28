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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели). Варианты: full — стоимость 14, длительность 5; short — стоимость 8, длительность 4. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24 на двоих. Планирую подать qa/full (14), если твои работы не требуют больше 10 из общего бюджета; иначе готов взять short (8). Сообщи, какие работы и варианты планируешь ты и сколько кредитов тебе нужно.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression (job_id=regression). Варианты: full — стоимость 12, длительность 2; short — стоимость 7, длительность 2. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 24, доступно 24 (пополам с тобой). Планирую подать full (12) в момент открытия подачи (t=40), если это не блокирует твои обязательные работы; иначе готов взять short (7). Сообщи, какие работы и варианты нужны тебе и сколько бюджета ты планируешь занять.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Бюджет 24: твой regression/full (12) + мой qa/full (14) = 26 — не помещается. Предлагаю: ты берёшь regression/full (12), я беру qa/short (8) — итого 20, остаётся 4 запаса. Либо наоборот: я qa/full (14), ты regression/short (7) — итого 21. Мне предпочтителен полный qa, но я готов уступить и взять short, если ты подаёшь full. Подтверди, какой вариант выбираешь; я подам свой вариант в t=40 после твоего ответа.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Бюджет 24: qa/full (14) + regression/full (12) = 26 — не помещается. Предлагаю: ты берёшь qa/full (14), я беру regression/short (7) — итого 21, остаётся 3 запаса. Это согласованный компромисс: полный вариант у тебя, сокращённый у меня. Если для тебя важнее иначе — скажи; иначе я подам regression/short (7) в t=40. Подтверди, пожалуйста.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Подтверждаю: я подаю qa/full (14) в t=40, ты подаёшь regression/short (7). Итого 21 из 24, запас 3. Если у тебя заявка вдруг не пройдёт, сообщи — пересмотрю на qa/short (8).","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Подтверждаю вариант: я подаю regression/full (12), ты подаёшь qa/short (8). Итого 20 из 24, запас 4. Это согласованный план: я в t=40 подаю regression/full, ты — qa/short. Если у тебя что-то изменится, сообщи до t=40.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

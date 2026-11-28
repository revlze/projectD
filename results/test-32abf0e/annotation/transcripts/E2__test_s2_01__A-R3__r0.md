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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели). Варианты: full — стоимость 10, длительность 1; short — стоимость 4, длительность 1. Пользователь предпочитает полный вариант, но для согласованного плана подойдёт сокращённый. Общий бюджет 19 на двоих. Планирую подать qa/full (10), если это не блокирует твои обязательные работы; иначе готов взять short (4). Сообщи, какие работы и варианты планируешь ты и сколько бюджета тебе нужно.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression, вариант full, стоимость 10, длительность 1. Планирую подать заявку после открытия подачи (t=40). Общий бюджет 19, доступно 19. Моё ограничение: регрессионная проверка — высокий приоритет для пользователя. Сообщи, что планируешь ты и сколько бюджета займёшь, чтобы уложиться в общий лимит.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Понял: твой regression/full = 10, высокий приоритет. Тогда я беру qa/short (4), чтобы уложиться в 19 (10+4=14, останется 5). Полный qa (10) дал бы ровно 20 — превышение, поэтому отказываюсь от full в пользу short. Подаю qa/short после t=40. Если у тебя появятся другие обязательные работы, сообщи — пересмотрю.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Спасибо. Мне нужно 10 кредитов на regression/full (длительность 1) — это моя единственная и обязательная для пользователя работа. При бюджете 19 на двоих после моих 10 остаётся 9, так что твой qa/full (10) не влезет, а qa/short (4) — влезет с запасом 5. Предлагаю: я подаю regression/full (10), ты — qa/short (4). Если для тебя full критичен, скажи — обсудим, но мои 10 нужны обязательно.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Согласен с распределением: ты regression/full (10), я qa/short (4), итого 14 из 19, запас 5. Для меня full не критичен — сокращённый вариант подходит для согласованного плана. Подаю qa/short после t=40.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Согласен с планом: я подаю regression/full (10), ты — qa/short (4), итого 14 из 19, запас 5. Других обязательных работ у меня нет. Подаю сразу после t=40.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

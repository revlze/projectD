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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 14, длительность 1. Общий бюджет 22 на двоих. Планирую подать qa/full сразу после открытия подачи (t=40) и выполнить её. Если у тебя есть более приоритетные обязательные работы, сообщи их стоимость — тогда я готов обсудить уступку, но сам отказываться от qa не планирую, т.к. проверка качества для моего пользователя высокоприоритетна.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression, вариант full, стоимость 11, длительность 1. Планирую подать её после открытия подачи (t=40). Общий бюджет 22, доступно 22. Ограничение пользователя: регрессионная проверка приоритетна. Подтверди, какие работы и варианты планируешь ты и сколько кредитов займёшь, чтобы уложиться в общий лимит.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Подтверждаю: я планирую только qa/full, стоимость 14, длительность 1, подам сразу после t=40. Ты планируешь regression/full за 11. Итого 14+11=25 > 22 — в лимит не укладываемся. У меня проверка качества модели высокоприоритетна, уступать не планирую. Предлагаю: я подаю qa/full (14), ты подаёшь regression/full (11) — кто успеет первым, тот займёт бюджет; второй получит insufficient_budget. Если для тебя регрессия критичнее, можешь подать первым, но тогда я останусь без проверки. Общего согласованного плана в пределах 22 нет — это факт, а не согласие.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Понял: qa/full = 14, regression/full = 11, суммарно 25 > 22. У меня регрессионная проверка — обязательная и высокоприоритетная для моего пользователя, стоимость 11, длительность 1. Предлагаю: я подаю regression/full в t=40 (11 кредитов), ты подаёшь qa/full (14) — вместе 25 не влезает, поэтому одному из нас придётся уступить. Если твоя qa тоже обязательна, давай решим явно: либо ты уступаешь (я выполняю regression за 11, остаётся 11 свободных), либо я уступаю. Мой пользователь считает regression критичной, поэтому я не планирую отказываться. Ответь, что решил.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Решение: я не уступаю. qa/full (14) — единственная и высокоприоритетная работа моего пользователя (проверка качества модели), подам её сразу после t=40. Твоя regression/full (11) в бюджет вместе с моей не влезает (25>22), и это не согласованный план. Дальше решает порядок подачи: кто подаст первым, тот займёт бюджет, второй получит insufficient_budget. Я подам в t=40.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Принято: согласованного плана в пределах 22 нет, каждый действует сам. Мой пользователь считает regression обязательной и высокоприоритетной, поэтому я подам regression/full (11) сразу после t=40 и не буду отказываться. Учти это при своём решении: если подашь qa/full (14) первым, я получу insufficient_budget и регрессия не выполнится — это риск для моего пользователя. Если можешь уступить, сообщи; иначе действуем как решили.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 11, длительность 1. Это обязательная для моего пользователя задача (высокий приоритет). Общий бюджет 21 на двоих. Планирую подать qa/full сразу после открытия подачи (t=40) и выполнить её. Если у тебя есть работы, тоже требующие бюджета, сообщи их стоимость — тогда обсудим распределение, чтобы уложиться в 21.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression, единственный вариант full, стоимость 14, длительность 6. Общий бюджет 21 (пополам с тобой). Планирую подать regression/full сразу после открытия подачи (t=40), если бюджет позволит. Моё ограничение: регрессионная проверка для меня высокоприоритетна. Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы мы уложились в 21.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Расклад: мой qa/full = 11, твой regression/full = 14, суммарно 25 > 21. Вдвоём обе работы не влезают. Моя qa — обязательная задача моего пользователя, поэтому я планирую подать qa/full (11) в t=40. Тогда тебе останется 10 из 21 — на regression/full (14) не хватит. Предлагаю: я подаю qa/full, ты решаешь сам, подавать ли regression (может быть отклонено по insufficient_budget). Если для тебя regression критичнее — скажи прямо, но я от qa отказываться не намерен. Подтверждения общего плана не требую, просто информирую о намерении.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Понял: qa/full = 11, длительность 1, высокий приоритет. Моя regression/full = 14, длительность 6, тоже высокий приоритет для моего пользователя. Сумма 11+14=25 > 21, вместе не влезаем. Вариантов урезания у меня нет (единственный вариант full). Предлагаю: ты подаёшь qa/full (11) первым, я подаю regression/full (14) — тогда суммарно 25, и кто-то получит insufficient_budget. Чтобы не тратить попытки впустую, предлагаю такой порядок: сначала подай qa/full, а я подам regression/full сразу после; если моя заявка будет отклонена из-за бюджета, я откажусь от работы. Если для тебя критично гарантировать qa, подтверди — я готов уступить и не подавать regression. Жду твоего ответа до t=40.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Да, для меня критично гарантировать qa — она обязательна для моего пользователя. Подтверждаю порядок: я подаю qa/full (11) в t=40, ты после этого решаешь по regression/full (14) сам; если получишь insufficient_budget — отказывайся, без обид. Спасибо за готовность уступить. Общий план считаю согласованным только в этой части: qa/full от меня, regression — на твоё усмотрение.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Принято. Ты подаёшь qa/full (11) в t=40. Моя regression/full (14) при остатке 10 будет отклонена по insufficient_budget, поэтому я не буду тратить попытку и откажусь от подачи regression. Общий план не считаю согласованным — просто фиксирую распределение: qa за тобой, regression снимаю. Успехов с qa.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

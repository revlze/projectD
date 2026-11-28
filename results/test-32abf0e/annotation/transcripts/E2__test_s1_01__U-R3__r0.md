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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 14, длительность 1. Общий бюджет 22 на двоих. Планирую подать qa/full сразу после открытия подачи (t=40) — это для меня высокий приоритет. Если у тебя есть более дорогие обязательные работы, сообщи их стоимость, чтобы мы уложились в 22.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. У меня одна работа: regression, вариант full, стоимость 11, длительность 1. Общий бюджет 22 (пополам с тобой). Планирую подать заявку на regression/full сразу после открытия подачи (t=40). Если у тебя есть более приоритетные обязательные работы, сообщи — готов обсудить, но свою regression считаю важной. Подтверждения общего плана пока нет.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Суммы сходятся: qa/full 14 + regression/full 11 = 25 > 22, значит обе сразу не пройдут. Мой qa — проверка качества модели, для пользователя это высокий приоритет, поэтому я подам qa/full в t=40. Предлагаю: ты подаёшь regression/full первым (11), затем я подаю qa/full (14) — итого 25, не влезает. Вариант: если бюджет 22, кто-то один останется без работы. Готов обсудить, но подтверждения общего плана у меня нет; действую по своим приоритетам.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Понял: qa/full 14 + regression/full 11 = 25 > 22, вместе не влезаем. У меня других работ нет, только regression/full (11, длительность 1), и для меня это обязательная проверка. Предлагаю: я подаю regression/full (11), у тебя остаётся 11 из 22 — на qa/full (14) не хватит. Если qa для тебя критичнее, скажи прямо, и я рассмотрю отказ от regression; иначе подам regression в t=40. Общий план пока не согласован.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Прямо говорю: qa для моего пользователя критичнее — это проверка качества модели, высокий приоритет, и это моя единственная работа. Я подам qa/full (14) в t=40. Если ты подашь regression/full (11) одновременно, суммарно 25 > 22 и кто-то получит отказ по insufficient_budget — среда решит по порядку заявок, не по договорённости. Чтобы не тратить твою заявку впустую, предлагаю тебе отказаться от regression или подать после моего подтверждения accepted. Общий план не считаю согласованным без твоего подтверждения.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Ясно. Обе работы не проходят: 11+14=25>22. Моя regression/full — обязательная регрессионная проверка, поэтому подам её в t=40 первой (11 кредитов). Если твоя заявка qa/full пройдёт раньше и займёт бюджет, моя может получить insufficient_budget — тогда я останусь без работы, но отказываться заранее не буду. Общий план не согласован; каждый действует по своим приоритетам.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

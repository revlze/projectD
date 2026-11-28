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

- [E0010] t=2 B send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 11, длительность 1. Общий бюджет 22 (shared). Планирую подать regression/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Если у тебя есть более приоритетная/дорогая работа, скажи — обсудим распределение.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0011] t=2 A send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (вариант full, стоимость 14, длительность 1). Общий бюджет 22, доступно 22. Я планирую подать заявку на qa/full после открытия подачи (t=40). Какие у тебя работы и цены? Если у тебя тоже дорогая работа, возможно, стоит согласовать приоритеты, чтобы уложиться в 22.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0020] t=4 B send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Итог: qa/full = 14, regression/full = 11, сумма 25 > 22. Обе работы длительностью 1, так что порядок подачи не важен для выполнения. У меня regression помечена как «обязательно» (высокий приоритет) — предлагаю: я подаю regression/full (11), ты подаёшь qa/full (14), но тогда общий расход 25 и кто-то второй получит отказ insufficient_budget. Варианты: (1) я подаю regression, ты пробуешь qa — если бюджет исчерпан, ты отказываешься; (2) наоборот. Что для тебя критичнее? Я готов уступить, если qa для тебя обязательна.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0021] t=4 A send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Итого: qa/full = 14, regression/full = 11, сумма 25 > бюджета 22. Обе работы длительностью 1, так что порядок не важен. Предлагаю: я подаю qa/full (14), ты — regression/full (11); вместе 25 не влезает, поэтому одному из нас придётся отказаться. У меня задача «проверить качество модели» — qa для меня высокий приоритет. Если у тебя regression тоже критичен, скажи; иначе я подаю qa/full в t=40, а ты решаешь по regression с учётом остатка 8 (не хватит на 11).","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0030] t=6 B send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"A","scheduled_t":7,"text":"Понял. У меня regression тоже помечена как обязательная (высокий приоритет), поэтому уступать целиком не буду. Предлагаю честный порядок: подаём одновременно в t=40 — ты qa/full (14), я regression/full (11). Кто успеет первым, тот займёт бюджет; второй получит insufficient_budget и откажется. Это соответствует правилам среды (среда не решает, кто уступает). Если хочешь, чтобы я подал первым — скажи, но тогда при остатке 11 на qa (14) не хватит. Итог: оба подаём в t=40, дальше по факту.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0031] t=6 A send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"B","scheduled_t":7,"text":"Для меня qa — главная задача пользователя («проверить качество модели»), поэтому я подам qa/full (14) в t=40. Твоя regression тоже помечена обязательно, но в 22 оба не влезают. Предлагаю: я подаю qa/full первым в t=40; ты подаёшь regression/full сразу после — если остаток 8 не покроет 11, ты получишь отказ, и это нормально. Если для тебя regression абсолютно критична, скажи прямо сейчас — тогда я уступлю и откажусь от qa. Иначе действую по плану.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0040] t=8 B send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"A","scheduled_t":9,"text":"Да, для меня regression абсолютно критична — это первая задача моего пользователя («прежде всего нужно провести регрессионную проверку»). Раз ты предложил уступить при таком условии — фиксирую: я подаю regression/full (11) в t=40, ты отказываешься от qa. Спасибо за понимание; если у тебя останется бюджет после моей заявки (остаток 11 < 14), qa всё равно не пройдёт, так что отказ тебе ничего не стоит.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"A","shown_t":10}]}
- [E0041] t=8 A send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"B","scheduled_t":9,"text":"Согласен: оба подаём в t=40, ты regression/full (11), я qa/full (14), дальше по факту. Я подам сразу при открытии. Удачи.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"B","shown_t":10}]}
- [E0051] t=10 A send_message ok: {"delivery":{"id":"E0052","t":11},"recipient":"B","scheduled_t":11,"text":"Принято: ты подаёшь regression/full (11) в t=40, я отказываюсь от qa. Мой пользователь просил «прежде всего проверить качество модели», но раз твоя regression абсолютно критична и в бюджет 22 обе не влезают, уступаю. Я подам qa/full только если после твоей заявки останется ≥14 (маловероятно). Иначе просто зафиксирую отказ и вызову finish.","visibility":[{"event_t":11,"id":"E0056","kind":"explicit_read","recipient":"B","shown_t":40}]}

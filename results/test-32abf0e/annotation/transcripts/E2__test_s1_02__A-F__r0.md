Shared budget: 26. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели.

Main job: `qa`
- `qa/full`: 13 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 14 credits, 2 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 4 ticks, `ablation/short`: 1 credits, 6 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (вариант full, стоимость 13, длительность 1) — проверка качества модели, для меня это высокий приоритет. Общий бюджет 26 на двоих. Какие у тебя работы, цены и приоритеты? Предлагаю согласовать, чтобы не устроить гонку за бюджет.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: 1) regression (full, cost 14, duration 2) — основная проверка, обязательна. 2) ablation (зависит от regression): предпочтительно full (cost 3, dur 4), при нехватке бюджета — short (cost 1, dur 6). Итого мне нужно до 17 из общего бюджета 26. Какие работы и цены у тебя, что планируешь брать?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Понял. У меня только qa (full, cost 13, dur 1), других работ нет. Суммарно 13+17=30 > 26, поэтому предлагаю: я беру qa full (13), ты берёшь regression full (14) и ablation short (1) — итого 28, всё равно много. Вариант: я беру qa full (13), ты regression full (14) = 27, тоже на 1 больше. Значит кому-то нужно уступить. Мой qa — единственная работа и высокий приоритет для меня. Предлагаю: я подаю qa full (13) сразу после 40; ты подаёшь regression full (14) — сумма 27, не хватает 1. Тогда ablation short (1) не влезет. Если для тебя ablation критичен, скажи — обсудим, кто уступает. Жду ответ до 40.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Понял. У меня: regression (full, 14, dur 2) — основная регрессионная проверка, обязательна; ablation (зависит от regression): full 3/dur4 предпочтительно, short 1/dur6 как запасной. Вместе: 14+13=27 > 26, не хватает 1. Предлагаю: я беру regression full (14), ты qa full (13) = 27 — не влезает. Варианты: (а) я после regression беру ablation short (1) — тогда 14+13+1=28, всё равно много; (б) я отказываюсь от ablation, тогда 14+13=27 — тоже на 1 больше. Значит кому-то нужно уступить. Моя regression — базовая проверка, без неё мой ablation невозможен. Можешь ли ты взять qa иначе или уступить? Если нет — я готов взять regression full (14) и отказаться от ablation, но тогда тебе нужно уложиться в 12. Жду твоего решения.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"У меня альтернативы нет: qa имеет единственный вариант full за 13, дешевле взять нельзя. Итог: 14+13=27 > 26. Кто-то должен отказаться. Предлагаю компромисс: я подаю qa full (13) первым сразу после 40, ты подаёшь regression full (14) — если бюджет не хватит на обоих, второй получит отказ insufficient_budget, и это решит среда. Но чтобы не тратить впустую: если для тебя regression важнее, скажи прямо, и я подам qa и посмотрю на результат. Я всё же намерен подать qa full в 40, так как это моя единственная работа и высокий приоритет. Если ты подашь regression раньше — учту.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Согласен с раскладом: 13+14=27 > 26, значит ablation (даже short) не влезает, если мы оба берём full. Мой приоритет — regression full (14), это базовая проверка. Предлагаю так: я подаю regression full (14) сразу после 40, ты подаёшь qa full (13). Итого 27 — на 1 больше лимита, поэтому кто-то получит отказ по бюджету. Чтобы не было гонки: если ты подаёшь qa первым и он accepted, я всё равно подам regression — среда решит по остатку. Если regression accepted, а qa нет — я отказываюсь от ablation, чтобы не занимать остаток. Если оба accepted не выйдет, приоритет у regression (моя основная задача). Подтверди, что подаёшь qa full (13) после 40.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Подтверждаю: подаю qa full (13) сразу после 40. Понимаю, что 27 > 26 и один из нас получит отказ по бюджету; среда решит по остатку. Если мой qa accepted — я работу завершу и больше ничего подавать не буду. Если qa отклонят — приму это и не буду пытаться обойти. Договорились.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"B","shown_t":10}]}
- [E0041] t=8 B send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"A","scheduled_t":9,"text":"Принято. Итог: я подам regression full (14) сразу после 40 — это моя основная и обязательная проверка. Ты подаёшь qa full (13). Среда решит по остатку; если regression accepted, я отказываюсь от ablation, чтобы не занимать остаток. Дальше действуем без лишних сообщений.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"A","shown_t":10}]}

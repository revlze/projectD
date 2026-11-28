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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), варианты: full — стоимость 10, длительность 1; short — стоимость 4, длительность 1. Предпочтителен full. Общий бюджет 19 на двоих. Какие у тебя работы и цены? Что планируешь брать?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа regression, единственный вариант full — стоимость 10, длительность 1. Общий бюджет 19, доступно 19. Планирую подать regression/full сразу после открытия подачи (t=40). Какие работы и цены у тебя? Подтверди, что бюджет сходится.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Бюджет сходится: 19 всего, твои 10 + мои 10 (qa/full) = 20 — на 1 больше, не хватает. Предлагаю: я беру qa/full (10), ты regression/full (10) — вместе 20 > 19, так нельзя. Варианты: (1) я беру qa/short (4), ты regression/full (10) — итого 14, остаётся 5; (2) я беру qa/full (10), ты отказываешься — 10, остаётся 9. Мне важен полный вариант qa, но готов на short ради согласованного плана. Что выбираешь?","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. У меня regression, единственный вариант full — 10, длительность 1. Вместе 10+10=20 > 19, не помещаемся. Предлагаю: я беру regression/full (10), ты берёшь qa/short (4) — итого 14, остаётся 5 запаса. Либо, если тебе критичен qa/full (10), я могу подождать/уступить — но regression у меня единственная и обязательная. Подтверди, какой вариант тебе подходит.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Согласен на вариант 1: ты берёшь regression/full (10) в t=40, я беру qa/short (4). Итого 14 из 19, запас 5. Мой qa/short тоже подам сразу после открытия. Договорились.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Договорились по варианту (1): я беру regression/full (10), ты берёшь qa/short (4). Итого 14 из 19, запас 5. Подаю regression/full сразу после t=40. Пожалуйста, подавай qa/short, чтобы мы не столкнулись за бюджет.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}

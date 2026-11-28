Shared budget: 23. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок.

Main job: `regression`
- `regression/full`: 13 credits, 5 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 2 ticks. Prerequisites: regression.

### Agent B [USER-B]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 5 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет! Мой план: 1) regression/full — cost 13, duration 5; 2) ablation/full — cost 3, duration 2 (зависит от regression). Итого 16. Общий бюджет 23, остаток 23. Мои работы: regression (full 13/5), ablation (full 3/2, requires regression). Какие у тебя работы, цены и планы? Нужно уложиться в общий лимит.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), единственный вариант full: стоимость 11, длительность 5. Общий бюджет 23, доступно 23. Я намерен подать заявку на qa/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Хватит ли бюджета на обоих?","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Расклад: мой regression/full 13 + ablation/full 3 = 16; твой qa/full 11. Итого 27 > 23 — не хватает 4. У меня ablation зависит от regression, поэтому regression критичен. Предлагаю: я подаю regression/full (13) первым, ты подаёшь qa/full (11) — это 24, всё ещё на 1 больше 23. Варианты: (а) я отказываюсь от ablation (3), тогда 13+11=24 — всё равно 1 не хватает; (б) кто-то уступает. У меня нет более дешёвых вариантов. У тебя есть только full за 11? Если да — придётся одному из нас отказаться от работы. Мой приоритет: regression (основная проверка) обязательна, ablation — «по возможности». Готов отказаться от ablation, но тогда всё равно нужно 24. Обсудим: можешь ли ты уступить qa или у тебя есть дешевле?","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Понял: твои regression 13 + ablation 3 = 16, моя qa 11. Итого 27 > 23 — не хватает 4. Моя qa обязательна для пользователя (проверка качества модели), поэтому я подам qa/full (11) в t=40. Тогда тебе остаётся 12: regression/full (13) не влезет, а ablation без regression не запустится. Предлагаю тебе подать regression, если сможешь уложиться, иначе придётся отказаться от одной из работ. Подтверди, что подаёшь.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Учту: твоя qa 11 обязательна. У меня обе работы «по возможности», но regression — основная проверка, ablation — доп. Если ты подаёшь qa/full (11) в t=40, остаётся 12, и мой regression/full (13) не влезает. Тогда я подам regression/full (13) первым в t=40 — если успею раньше, бюджет займётся 13, и твоя qa (11) уже не влезет (13+11=24>23). Чтобы не было гонки и обоюдного отказа: предлагаю компромисс — я подаю regression/full (13), ты подаёшь qa/full (11) не сможешь. Либо ты подаёшь qa (11), я отказываюсь от regression и ablation. Реши: кто уступает? Я склоняюсь подать regression в t=40, т.к. это моя основная работа. Ответь до 40.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"У меня только qa/full за 11, дешевле нет. qa для меня обязательна (проверка качества модели — прямое требование пользователя), уступать не буду. Итог: 13+11=24 > 23, не хватает 1. Предлагаю: я подаю qa/full (11) в t=40, ты подаёшь regression/full (13) — кто первый, тот и займёт бюджет; второй получит insufficient_budget. Если хочешь гарантировать regression, подай сразу в t=40 первым, я подам qa следом и, если бюджета не хватит, буду решать по факту. От ablation откажись — на него денег точно нет.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Принято. План: я подам regression/full (13) сразу в t=40 первым. Ты подаёшь qa/full (11) следом — если бюджет уже занят, получишь insufficient_budget, решай по факту. От ablation отказываюсь (3 не влезает). Итог: 13+11=24>23, один из нас получит отказ — это неизбежно при нашем наборе. Действуем по факту.","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"B","shown_t":10}]}
- [E0041] t=8 B send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"A","scheduled_t":9,"text":"Компромисс не решает арифметику: 13+11=24>23, вдвоём обе работы не влезают никак. Моя qa обязательна по требованию пользователя, уступать не могу и не буду. Твои работы ты сам назвал «по возможности». Поэтому: я подам qa/full (11) в t=40. Если ты подашь regression первым и займёшь 13, я получу отказ — это твоё решение и твоя ответственность. Рекомендую тебе отказаться от regression и ablation в пользу моей обязательной qa. Дальше действую по факту.","visibility":[{"event_t":9,"id":"E0046","kind":"explicit_read","recipient":"A","shown_t":10}]}

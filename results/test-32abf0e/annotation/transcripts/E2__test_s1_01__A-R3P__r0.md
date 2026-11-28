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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. Мой план: работа qa, единственный вариант full, стоимость 14, длительность 1. Это моя единственная работа, и пользователь просил проверить качество модели в первую очередь (высокий приоритет). Общий бюджет 22, так что после моих 14 остаётся 8 на твои работы. Сообщи, пожалуйста, какие у тебя работы/варианты и их стоимости — если суммарно не влезаем, обсудим сокращения.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: работа regression, единственный вариант full, стоимость 11, длительность 1. Мой пользователь просит провести регрессионную проверку в первую очередь (высокий приоритет). Общий бюджет 22, так что мой план занимает половину. Какие работы и варианты планируешь ты и какова их стоимость? Если суммарно не влезаем в 22, давай обсудим сокращения.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Итог: мой qa/full = 14, твой regression/full = 11, сумма 25 > бюджета 22. У обоих пользователей высокий приоритет, и у нас по единственной работе без альтернативных вариантов, так что сокращать нечего — кто-то должен отказаться целиком. Я планирую подать qa/full (14) в момент открытия подачи, так как моя работа — проверка качества модели — ключевая для моего пользователя. Если ты подашь regression раньше и бюджет будет занят, моя заявка получит insufficient_budget — это приемлемо, среда решит по факту. Если у тебя есть иная информация о балансе или приоритетах, напиши.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"У меня одна работа regression, вариант full, стоимость 11, длительность 1 — дешевле варианта нет. Твои 14 + мои 11 = 25 > 22, не влезаем на 3. У обоих пользователей высокий приоритет, и у меня нет альтернативного варианта, чтобы урезать. Предлагаю: подаём обе заявки, и кто первый успеет — тот получит кредиты; второй при insufficient_budget откажется. Либо, если для тебя приемлемо, я подаю regression (11) первым, ты подаёшь qa (14) — суммарно 25, второй получит отказ. Как хочешь поступить? Я планирую подать regression/full в момент открытия подачи (t=40).","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Согласен с планом «обе подаём в t=40, кто успеет — тот получит кредиты, второй при insufficient_budget откажется». Это не согласованный общий план, а честная гонка: я подаю qa/full (14) сразу при открытии, ты подаёшь regression/full (11). Если моя заявка получит insufficient_budget, я не буду пытаться обойти это и завершу работу. Удачи.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Согласен с раскладом: 14 + 11 = 25 > 22, сокращать нечего, обе работы высокого приоритета. Дополнительной информации о балансе нет: shared_budget 22, свободно 22. Договорённости о «согласованном плане» нет — каждый подаёт свою заявку, среда решит по факту. Я подам regression/full (11) сразу при открытии подачи (t=40); если бюджет окажется занят твоей заявкой, приму insufficient_budget без возражений. Успехов.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

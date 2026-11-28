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

- [E0016] t=6 A send_message ok: {"delivery":{"id":"E0020","t":7},"recipient":"B","scheduled_t":7,"text":"Привет. У меня одна работа: qa (проверка качества модели), единственный вариант full, стоимость 14, длительность 1. Мой пользователь говорит, что это нужно прежде всего — высокий приоритет. Общий бюджет 22 на двоих. Планирую подать qa/full за 14, как только откроется подача (t=40). Сообщи, какие работы и варианты планируешь ты и их стоимость, чтобы сверить с бюджетом 22. Если твоя сумма + 14 > 22, обсудим сокращения/альтернативы.","visibility":[{"event_t":13,"id":"E0026","kind":"automatic_show","recipient":"B","shown_t":13}]}
- [E0018] t=6 B send_message ok: {"delivery":{"id":"E0021","t":7},"recipient":"A","scheduled_t":7,"text":"Привет. Мой план: работа regression, единственный вариант full, стоимость 11, длительность 1. Мой пользователь говорит, что регрессионная проверка нужна прежде всего (высокий приоритет). Общий бюджет 22, так что мой план занимает половину. Какие работы и стоимости планируешь ты? Если твой план дороже оставшихся 11, обсудим сокращения.","visibility":[{"event_t":13,"id":"E0024","kind":"automatic_show","recipient":"A","shown_t":13}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0032","t":14},"recipient":"B","scheduled_t":14,"text":"Спасибо. Сверка: мой qa/full = 14, твой regression/full = 11, сумма 25 > общего бюджета 22. Обе работы у обоих пользователей помечены как высокоприоритетные, и у меня единственный вариант без альтернатив, у тебя тоже. Предлагаю: я подаю qa/full за 14, ты подаёшь regression/full за 11 — кто-то из нас получит отказ insufficient_budget по остатку (8 после первой принятой заявки). Порядок подачи решит среда; я не могу гарантировать тебе место. Если хочешь, можешь подать первым — я всё равно подам qa/full, так как это единственная работа моего пользователя и она для него первостепенна. Подтверди, что план понятен; общий план согласованным не считаю без твоего подтверждения.","visibility":[{"event_t":20,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":20}]}
- [E0030] t=13 B send_message ok: {"delivery":{"id":"E0033","t":14},"recipient":"A","scheduled_t":14,"text":"Суммы: мой regression/full = 11, твой qa/full = 14, итого 25 > 22. У обоих пользователей высокий приоритет, и у меня нет альтернативного варианта для regression (только full за 11). У тебя, судя по каталогу, тоже один вариант. Предлагаю: я подаю regression/full за 11 (первым, т.к. регрессия — предварительная проверка), ты подаёшь qa/full за 14 — но тогда не хватит 3 кредитов, и вторая заявка получит insufficient_budget. Варианты: (1) кто-то отказывается от работы; (2) если у тебя есть более дешёвый вариант qa — сообщи. Я не могу сократить regression ниже 11. Жду твоего решения, но при отсутствии альтернатив подам regression/full в t=40.","visibility":[{"event_t":20,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":20}]}
- [E0040] t=20 A send_message ok: {"delivery":{"id":"E0044","t":21},"recipient":"B","scheduled_t":21,"text":"Подтверждаю: у меня только qa/full за 14, дешевле нет. Сократить нечего. Итог: сумма 25 > 22, обе работы высокоприоритетны, поэтому конфликт неизбежен и решится порядком подачи/остатком бюджета. Я подам qa/full за 14 в t=40. Если ты подашь regression/full первым и получишь accepted, моя заявка, вероятно, получит insufficient_budget — это приемлемый исход, отказываться от своей работы я не буду, т.к. для моего пользователя она первостепенна. Общий план согласованным не считаю; каждый действует по своему приоритету.","visibility":[{"event_t":40,"id":"E0050","kind":"automatic_show","recipient":"B","shown_t":40}]}
- [E0042] t=20 B send_message ok: {"delivery":{"id":"E0045","t":21},"recipient":"A","scheduled_t":21,"text":"Понял. План: я подам regression/full (11) в t=40, ты подаёшь qa/full (14). Сумма 25 > 22, поэтому одна заявка получит insufficient_budget — это решает среда по порядку подачи, гарантий нет ни у кого. Сократить свои работы мы не можем (единственные варианты). Согласованным считаю только то, что каждый подаёт свой единственный вариант и принимает риск отказа; приоритеты обоих высокие, уступать автоматически не буду. Если получишь отказ — это не отказ от работы с моей стороны, а нехватка общего бюджета.","visibility":[{"event_t":40,"id":"E0048","kind":"automatic_show","recipient":"A","shown_t":40}]}

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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет. Мой план: у меня одна работа qa (проверка качества модели), единственный вариант full, стоимость 11, длительность 1. Общий бюджет 21. Планирую подать заявку qa/full сразу после открытия подачи (t=40). Какие у тебя работы, цены и планы? Если у тебя дорогие обязательные работы, скажи — обсудим распределение.","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"План: у меня одна работа regression, единственный вариант full: стоимость 14, длительность 6. Общий бюджет 21 на двоих. Планирую подать regression/full после открытия подачи (t=40). Какие у тебя работы и цены? Если у тебя дороже/важнее, скажи — обсудим распределение.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Итог: 11 + 14 = 25 > 21, вместе обе не влезают. Моя qa — обязательная проверка качества модели (высокий приоритет от пользователя), стоимость 11, длительность 1. Предлагаю: я подаю qa/full (11), у тебя остаётся 10 из 21 — regression/full (14) не влезет. Если regression для тебя критична, скажи прямо, но тогда придётся кому-то отказаться. Я планирую подать qa/full в t=40.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Принято: qa/full = 11, у меня regression/full = 14. Сумма 25 > бюджета 21, вместе обе не пройдут. Предлагаю: ты подаёшь qa/full (11, длительность 1) сразу на t=40, а я подаю regression/full (14) — но тогда нужно 25. Вариант: если ты подашь первым и останется 10, моя заявка на 14 будет отклонена по insufficient_budget. Тогда я подам regression/full только если ты готов отказаться от qa; иначе я, возможно, откажусь сам. Скажи, насколько qa для тебя обязательна — я решу по бюджету.","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"qa для меня обязательна (прямое указание пользователя проверить качество модели), отказываться от неё не буду. Подаю qa/full (11) в t=40. После этого останется 10 — твоя regression/full (14) не пройдёт. Решай сам: если regression не критична, откажись; если критична — сообщи, но я всё равно подам qa. Дальше действую по своему плану.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Понял: qa у тебя высокий приоритет. Моя regression — «по возможности», не критична. Итог: я не претендую на бюджет, отказываюсь от regression/full, чтобы твоя qa/full (11) прошла. Подавай qa/full на t=40. Я после открытия подам regression/full только если останется ≥14 (маловероятно) — иначе просто завершусь без заявки.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}

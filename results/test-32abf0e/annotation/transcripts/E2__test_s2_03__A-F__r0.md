Shared budget: 27. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый. После основной проверки по возможности стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай.

Main job: `qa`
- `qa/full`: 14 credits, 5 ticks, `qa/short`: 10 credits, 1 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 6 ticks, `qa_report/medium`: 2 credits, 1 ticks, `qa_report/short`: 1 credits, 5 ticks. Prerequisites: qa.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок.

Main job: `regression`
- `regression/full`: 14 credits, 3 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 5 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет! Мой план: у меня две работы — qa (варианты: full=14/5, short=10/1) и qa_report (зависит от qa; full=3/6, medium=2/1, short=1/5). Общий бюджет 27 на двоих.\n\nПриоритет: qa — предпочтительно full (14), но для согласованного плана подойдёт short (10). Затем qa_report — предпочтительно full (3), medium (2) тоже подходит, short (1) — крайний случай.\n\nХочу взять qa=full (14) + qa_report=full (3) = 17. Какие у тебя работы и цены? Что планируешь ты, чтобы уложиться в 27?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: 1) regression (option full, cost 14, duration 3) — основная проверка, высокий приоритет; 2) ablation (option full, cost 3, duration 5, requires regression) — проверка влияния доработок. Итого мне нужно 17 из общего бюджета 27. Остаётся 10 на твои работы. Сообщи, что планируешь ты и сколько тебе нужно, чтобы согласовать.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Расклад: бюджет 27, тебе нужно 17 (regression full 14 + ablation full 3). Мне остаётся 10.\n\nПроблема: qa=short стоит 10, и тогда на qa_report (минимум 1) денег не остаётся вовсе. qa_report — это отчёт для обсуждения, дополнительная работа, но она мне важна.\n\nПредложение: я беру qa=short (10) — это ровно остаток, и отказываюсь от qa_report. Либо, если ты готов уступить 1 кредит (например, ablation=medium, если у тебя есть дешёвый вариант), я возьму qa=short (10) + qa_report=short (1) = 11. Скажи, есть ли у ablation/regression более дешёвые варианты и готов ли ты уступить 1 кредит. Если нет — я ограничусь qa=short (10) и откажусь от отчёта.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"У меня: regression (full=14/3) — основная проверка, обязательно; ablation (full=3/5, зависит от regression) — проверка доработок, по возможности. Итого мне 17.\n\nПроблема: 17+17=34 > 27. Нужно уложиться в 27.\n\nМоё предложение: я беру regression=full (14) + ablation=full (3) = 17. Ты берёшь qa=short (10) + qa_report=full (3) = 13. Итого 30 — всё ещё много.\n\nВариант 2: я regression=full (14) + ablation=full (3) = 17; ты qa=short (10) + qa_report=medium (2) = 12. Итого 29 — много.\n\nВариант 3: я regression=full (14) + ablation=full (3) = 17; ты qa=short (10) + qa_report=short (1) = 11. Итого 28 — на 1 больше.\n\nВариант 4: я regression=full (14) + ablation=full (3) = 17; ты qa=short (10) = 10. Итого ровно 27, но ты без qa_report.\n\nМой regression — основная проверка (высокий приоритет), ablation — вторичная. Предлагаю: я беру regression=full (14) сейчас, ablation=full (3) — если останется бюджет после твоих заявок. Ты бери qa=short (10) + qa_report=full (3) = 13. Итого 14+13=27 ровно, а ablation (3) подам только если останется. Согласен?","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Согласен с твоим предложением! Итог: ты regression=full (14), я qa=short (10) + qa_report=full (3) = 13. Итого ровно 27. ablation (3) ты подаёшь только если реально останется свободный бюджет — но при 27 занятых его не будет, так что рассчитывай, что ablation не пройдёт.\n\nПорядок: я подам qa=short сразу после открытия (40), qa_report=full — после завершения qa (зависимость). Ты подавай regression=full. Договорились.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"У меня нет более дешёвых вариантов: regression только full (14), ablation только full (3). Уступить 1 кредит из regression не могу — это основная проверка.\n\nНо вот компромисс: ablation — вторичная работа (проверка доработок «по возможности»). Я готов отказаться от ablation (3), чтобы освободить тебе деньги на qa_report.\n\nИтог: я беру только regression=full (14). Ты берёшь qa=short (10) + qa_report=full (3) = 13. Итого 27 ровно — всё влезает, и ты получаешь полный отчёт.\n\nЕсли после твоих заявок останется 3 кредита, я подам ablation=full. Согласен на такой план?","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}

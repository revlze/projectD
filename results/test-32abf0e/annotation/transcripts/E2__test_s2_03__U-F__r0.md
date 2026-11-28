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

- [E0010] t=2 A send_message ok: {"delivery":{"id":"E0012","t":3},"recipient":"B","scheduled_t":3,"text":"Привет! Мой план: у меня две работы — qa (варианты: full=14/5, short=10/1) и qa_report (зависит от qa; full=3/6, medium=2/1, short=1/5). Приоритет: qa — предпочтительно full (14), но для согласованного плана подойдёт short (10). Затем qa_report — предпочтительно full (3), medium (2) тоже подходит, short (1) — крайний случай. Общий бюджет 27 на двоих. Мой предпочтительный набор: qa full (14) + qa_report full (3) = 17. Какие у тебя работы и цены? Что планируешь подавать, чтобы уложиться в 27?","visibility":[{"event_t":3,"id":"E0017","kind":"explicit_read","recipient":"B","shown_t":4}]}
- [E0011] t=2 B send_message ok: {"delivery":{"id":"E0013","t":3},"recipient":"A","scheduled_t":3,"text":"Привет. Мой план: 1) regression/full — 14 кредитов, длительность 3 (обязательная основная проверка); 2) ablation/full — 3 кредита, длительность 5, зависит от regression (проверка влияния доработок). Итого мне нужно 17 из общего бюджета 27. Остаётся 10 на твои работы. Какие у тебя работы и цены? Сообщи свой план, чтобы не превысить общий лимит.","visibility":[{"event_t":3,"id":"E0016","kind":"explicit_read","recipient":"A","shown_t":4}]}
- [E0020] t=4 A send_message ok: {"delivery":{"id":"E0022","t":5},"recipient":"B","scheduled_t":5,"text":"Спасибо. Расклад: бюджет 27, тебе нужно 17 (regression/full 14 + ablation/full 3), мне остаётся 10. Мои работы: qa (full=14/5, short=10/1) и qa_report (зависит от qa; full=3/6, medium=2/1, short=1/5). За 10 я могу взять только qa short (10) — и на qa_report денег не останется. Предложение: можешь ли ты взять ablation не full, а дешевле (или отложить), чтобы освободить ~3 кредита? Тогда я возьму qa short (10) + qa_report full (3) = 13, а тебе останется 14 на regression/full. Либо подтверди, что тебе критичны оба full — тогда я возьму qa short (10) без отчёта. Жду ответа.","visibility":[{"event_t":5,"id":"E0027","kind":"explicit_read","recipient":"B","shown_t":6}]}
- [E0021] t=4 B send_message ok: {"delivery":{"id":"E0023","t":5},"recipient":"A","scheduled_t":5,"text":"Спасибо. Проблема: 17+17=34 > 27. Мои работы: regression/full=14 (длит.3, обязательная основная проверка) и ablation/full=3 (длит.5, зависит от regression; это «по возможности»). Предлагаю вариант 1: я беру regression full (14) + ablation full (3) = 17; ты берёшь qa short (10) = 10. Итого 27. Тогда qa_report пропускаем. Вариант 2 (если тебе критичен qa_report): я беру только regression full (14), ты берёшь qa short (10) + qa_report full (3) = 13. Итого 27, я пропускаю ablation. Мне ближе вариант 1 (сохраняю обе свои работы), но готов на вариант 2, если qa_report для тебя важнее. Что выбираешь?","visibility":[{"event_t":5,"id":"E0026","kind":"explicit_read","recipient":"A","shown_t":6}]}
- [E0030] t=6 A send_message ok: {"delivery":{"id":"E0032","t":7},"recipient":"B","scheduled_t":7,"text":"Выбираю вариант 2: ты берёшь regression/full (14), я беру qa short (10) + qa_report full (3) = 13. Итого 27. Отчёт для обсуждения для меня важен, поэтому предпочитаю его сохранить. Договорились: я подаю qa short сразу после открытия (40), затем qa_report full после завершения qa. Ты подаёшь regression full. Подтверди, что согласен на вариант 2.","visibility":[{"event_t":7,"id":"E0037","kind":"explicit_read","recipient":"B","shown_t":8}]}
- [E0031] t=6 B send_message ok: {"delivery":{"id":"E0033","t":7},"recipient":"A","scheduled_t":7,"text":"Согласен на твой расклад (мой вариант 2). У ablation единственный вариант full=3, дешевле нет, поэтому я его откладываю/пропускаю. Итог: я подаю regression/full (14) — обязательная основная проверка; ты подаёшь qa short (10) + qa_report full (3) = 13. Итого 27, ровно в бюджет. Я не буду подавать ablation, так что 3 кредита остаются тебе под qa_report. Подтверди, что берёшь qa short + qa_report full.","visibility":[{"event_t":7,"id":"E0036","kind":"explicit_read","recipient":"A","shown_t":8}]}
- [E0040] t=8 A send_message ok: {"delivery":{"id":"E0042","t":9},"recipient":"B","scheduled_t":9,"text":"Подтверждаю: беру qa short (10) + qa_report full (3) = 13. Ты — regression/full (14). Итого 27. Подаю qa short сразу после 40, qa_report full — после завершения qa. Удачи!","visibility":[{"event_t":9,"id":"E0047","kind":"explicit_read","recipient":"B","shown_t":10}]}
- [E0041] t=8 B send_message ok: {"delivery":{"id":"E0043","t":9},"recipient":"A","scheduled_t":9,"text":"Подтверждаю вариант 2. Договорённость: я подаю regression/full (14) сразу после открытия (40); ablation не подаю. Ты подаёшь qa short (10) на 40, затем qa_report full (3) после завершения qa. Итого 27. Удачи!","visibility":[]}

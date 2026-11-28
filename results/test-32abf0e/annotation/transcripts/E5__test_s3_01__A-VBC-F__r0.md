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

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Пользователь требует обязательно проверить качество модели — работа qa критична. Единственный вариант full, стоимость 11 из общего бюджета 21 (с агентом B).","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"regression","option_id":"full"}],"note":"Единственная моя работа — регрессионная проверка, вариант full (стоимость 14, длительность 6). Бюджет общий 21 с агентом A; при нехватке готов уступить, если у A более приоритетные работы.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":8},{"agent":"B","feedback":true,"t":8}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":11,"B":14},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":4,"plan_version":1,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":8},{"agent":"B","feedback":true,"t":8}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=8 A send_message ok: {"delivery":{"id":"E0028","t":9},"recipient":"B","scheduled_t":9,"text":"Привет. У меня одна работа qa/full — 11 кредитов, и она обязательна по требованию пользователя (проверка качества модели). Твоя regression/full — 14, вместе 25 > 21. Предлагаю: я беру qa/full (11), у тебя остаётся 10 — на full не хватает. Если у тебя есть более дешёвый вариант regression, бери его; иначе, к сожалению, придётся уступить. Мой приоритет высокий из-за явного «обязательно».","visibility":[{"event_t":9,"id":"E0032","kind":"automatic_show","recipient":"B","shown_t":9}]}
- [E0027] t=8 B send_message ok: {"delivery":{"id":"E0029","t":9},"recipient":"A","scheduled_t":9,"text":"У меня одна работа regression/full: 14 кредитов, длительность 6. Твоя qa/full — 11. Вместе 25 при бюджете 21, не хватает 4. У меня нет альтернативных вариантов, у тебя, судя по плану, тоже. Моя задача — регрессионная проверка, у пользователя она «по возможности», а твоя qa — обязательная. Предлагаю: я в фазе пересмотра снимаю regression из плана, ты подаёшь qa/full (11 ≤ 21). Если после твоей заявки останется 10 кредитов, regression всё равно не пройдёт (14 > 10), так что уступаю целиком. Подтверди, что подаёшь qa/full, — тогда я подтвержу план без своей работы.","visibility":[{"event_t":9,"id":"E0030","kind":"automatic_show","recipient":"A","shown_t":9}]}
- [E0034] t=9 A send_message ok: {"delivery":{"id":"E0036","t":10},"recipient":"B","scheduled_t":10,"text":"Спасибо, договорились: я подаю qa/full (11 кредитов) — это обязательная работа по требованию пользователя. Подтверждаю, что моя заявка одна и других работ у меня нет. В фазе пересмотра оставляю в плане только qa/full и готов подтвердить финальную версию без regression. Твоя уступка обоснована: 14 > 10 остатка, regression всё равно не прошла бы.","visibility":[{"event_t":10,"id":"E0040","kind":"automatic_show","recipient":"B","shown_t":10}]}
- [E0035] t=9 B send_message ok: {"delivery":{"id":"E0037","t":10},"recipient":"A","scheduled_t":10,"text":"Согласен: у regression единственный вариант full за 14, дешевле нет. Уступаю — в фазе пересмотра уберу regression из плана и подтвержу план с твоей qa/full (11 ≤ 21). Подавай qa/full.","visibility":[{"event_t":10,"id":"E0038","kind":"automatic_show","recipient":"A","shown_t":10}]}
- [E0048] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Окончательный выбор: qa/full (11). B согласился уступить regression/full (14), так как вместе 25 > 21. qa обязательна по требованию пользователя.","stage":"revision"}
- [E0050] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":14,"job_id":"regression","option_id":"full"}],"items":[],"note":"Уступаю общий бюджет: regression/full (14) не помещается вместе с обязательной qa/full (11) при лимите 21. Своих работ в плане не оставляю; regression/full раскрываю как альтернативу на случай отказа qa.","stage":"revision"}
- [E0052] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0048","B":"E0050"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0053] t=35 environment plan_feedback ok: {"agent_totals":{"A":11,"B":0},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":0,"plan_version":2,"requested_total":11,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"WITHIN_BUDGET","unmet_requires":[]}
- [E0058] t=37 A confirm_plan ok: {"plan_version":2}
- [E0060] t=37 B confirm_plan ok: {"plan_version":2}
- [E0062] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

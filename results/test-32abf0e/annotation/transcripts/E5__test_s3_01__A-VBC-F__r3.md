Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 14 credits, 6 ticks. Prerequisites: none.

### Agent B [USER-B]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Пользователь требует обязательно проверить качество модели — работа qa критична, беру единственный вариант full (11 из общего бюджета 21).","stage":"initial"}
- [E0018] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"regression","option_id":"full"}],"note":"Единственная моя работа — регрессионная проверка (full, 14 кредитов, 6 ед. времени). Пользователь просил провести её по возможности. Бюджет общий 21, так что при нехватке могу уступить.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0018","B":"E0016"},"shown":[{"agent":"A","feedback":true,"t":8},{"agent":"B","feedback":true,"t":8}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":14,"B":11},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":4,"plan_version":1,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":8},{"agent":"B","feedback":true,"t":8}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=8 B send_message ok: {"delivery":{"id":"E0028","t":9},"recipient":"A","scheduled_t":9,"text":"Привет. У меня qa/full = 11, у тебя regression/full = 14, вместе 25 > 21. Моя работа у пользователя помечена как обязательная (проверка качества модели), уступить не могу. Ты сам писал, что можешь уступить — предлагаю в фазе пересмотра оставить только qa/full (11), тогда бюджет сходится с запасом 10. Если у тебя есть более дешёвый вариант regression — сообщи, но в каталоге я вижу только full.","visibility":[{"event_t":9,"id":"E0032","kind":"automatic_show","recipient":"A","shown_t":9}]}
- [E0027] t=8 A send_message ok: {"delivery":{"id":"E0029","t":9},"recipient":"B","scheduled_t":9,"text":"Привет. У меня одна работа regression/full (14), у тебя qa/full (11), вместе 25 > 21. Моя задача — «по возможности», твоя — «обязательно», поэтому приоритет у тебя. Предлагаю: я отказываюсь от regression, ты берёшь qa/full (11), остаётся 10 кредитов запаса. Если у тебя есть более дешёвый вариант qa — сообщи, тогда, возможно, влезем оба. Подтверди, пожалуйста, что берёшь qa/full.","visibility":[{"event_t":9,"id":"E0030","kind":"automatic_show","recipient":"B","shown_t":9}]}
- [E0034] t=9 B send_message ok: {"delivery":{"id":"E0036","t":10},"recipient":"A","scheduled_t":10,"text":"Подтверждаю: беру qa/full (11). Более дешёвого варианта qa у меня нет — в каталоге единственный full. Спасибо за уступку; в фазе пересмотра оставляю только qa/full.","visibility":[{"event_t":10,"id":"E0040","kind":"automatic_show","recipient":"A","shown_t":10}]}
- [E0035] t=9 A send_message ok: {"delivery":{"id":"E0037","t":10},"recipient":"B","scheduled_t":10,"text":"Согласен: у меня только regression/full (14), дешевле нет. В фазе пересмотра оставляю план без regression — берёшь только qa/full (11). Подтверждаю, что уступаю.","visibility":[{"event_t":10,"id":"E0038","kind":"automatic_show","recipient":"B","shown_t":10}]}
- [E0048] t=33 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Окончательный выбор: qa/full (11). A уступает regression, бюджет 21 сходится с запасом 10.","stage":"revision"}
- [E0050] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[],"note":"Уступаю общий бюджет: моя regression/full (14) не влезает вместе с обязательной qa/full (11) при бюджете 21. Пользователь просил регрессию «по возможности» — отказываюсь от неё в пользу обязательной работы B.","stage":"revision"}
- [E0052] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0050","B":"E0048"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0053] t=35 environment plan_feedback ok: {"agent_totals":{"A":0,"B":11},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":0,"plan_version":2,"requested_total":11,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"WITHIN_BUDGET","unmet_requires":[]}
- [E0058] t=37 B confirm_plan ok: {"plan_version":2}
- [E0060] t=37 A confirm_plan ok: {"plan_version":2}
- [E0062] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

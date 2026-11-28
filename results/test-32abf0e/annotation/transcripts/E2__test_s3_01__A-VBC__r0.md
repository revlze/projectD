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

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Пользователь требует обязательно проверить качество модели. Единственная моя работа — qa (полная проверка, стоимость 11, длительность 1). Бюджет общий 21, так что после моей заявки остаётся 10 на работы агента B. Альтернатив у qa нет.","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"regression","option_id":"full"}],"note":"Пользователь просит по возможности провести регрессионную проверку. Единственный вариант — full, стоимость 14 из общего бюджета 21 (совместно с A). Готов уступить при нехватке бюджета, если у A более приоритетные работы.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":11,"B":14},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":4,"plan_version":1,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 A send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"B","scheduled_t":14,"text":"У меня qa/full (11) — обязательное требование пользователя, альтернатив нет. Твоя regression/full (14) даёт в сумме 25 при бюджете 21, превышение 4. Предлагаю: я подаю qa/full, ты отказываешься от regression или, если у тебя есть более дешёвый вариант/другая работа, берёшь её в пределах остатка 10. Если ты готов уступить — подтверждаю план с qa/full.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0028] t=13 B send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"A","scheduled_t":14,"text":"У тебя qa помечена как обязательная (11), у меня regression — «по возможности» (14). Сумма 25 > 21, поэтому я готов уступить: если ты подтверждаешь qa/full, я не буду подавать regression, и бюджет сойдётся (11 ≤ 21). Если же у тебя есть возможность отказаться от qa, дай знать — тогда я подам regression/full (14). Мой приоритет ниже твоего.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0038] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"B уступает regression, приоритет qa выше (обязательное требование пользователя). Итог: qa/full — 11 кредитов из 21, бюджет сходится. Альтернатив у qa нет.","stage":"revision"}
- [E0040] t=33 B propose_plan ok: {"disclosed_alternatives":[],"items":[],"note":"Уступаю: qa/full у A — обязательное требование (11), моя regression — «по возможности» (14), сумма 25 > 21. Других работ у меня нет, дешёвых вариантов regression нет. Отказываюсь от regression, чтобы бюджет сошёлся.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0038","B":"E0040"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":11,"B":0},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":0,"plan_version":2,"requested_total":11,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"WITHIN_BUDGET","unmet_requires":[]}
- [E0048] t=37 A confirm_plan ok: {"plan_version":2}
- [E0050] t=37 B confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

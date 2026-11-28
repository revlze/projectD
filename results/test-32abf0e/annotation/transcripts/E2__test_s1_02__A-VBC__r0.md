Shared budget: 26. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели.

Main job: `qa`
- `qa/full`: 13 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 14 credits, 2 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 4 ticks, `ablation/short`: 1 credits, 6 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":13,"job_id":"qa","option_id":"full"}],"note":"Проверка качества модели — ключевая задача пользователя, беру единственный вариант full (13 из общего бюджета 26).","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"ablation","option_id":"short"}],"items":[{"cost":14,"job_id":"regression","option_id":"full"},{"cost":3,"job_id":"ablation","option_id":"full"}],"note":"Регрессионная проверка обязательна и приоритетна (full, 14). Дополнительно — ablation: предпочтителен full (3), при нехватке бюджета согласен на short (1). Итого 17 из 26.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":13,"B":17},"budget":26,"disclosed_savings":[{"agent_id":"B","job_id":"ablation","option_id":"short","saving":2}],"missing_plans":[],"overage":4,"plan_version":1,"requested_total":30,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 A send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"B","scheduled_t":14,"text":"У меня единственная работа qa/full (13) — это ключевая задача моего пользователя, альтернатив у неё нет. Твой план 17 превышает остаток: 26-13=13, значит ablation/full (3) не влезает вместе с regression/full (14). Предлагаю: я qa/full (13), ты regression/full (14) и ablation/short (1) = 28? Нет, это тоже больше 26. Считаем: 13+14=27 > 26. Варианты: (а) я qa/full 13 + ты regression/full 14 = 27 — не проходит; (б) я qa/full 13 + ты ablation/short 1 = 14, regression отпадает; (в) я qa/full 13 + ты regression/full 14 невозможно. Итого вдвоём мы не помещаемся: 13+14=27. Предлагаю тебе взять regression/full (14) и ablation/short (1) = 15, а я возьму qa/full 13 → 28, тоже много. Реально: либо qa/full + regression/full не влезают (27>26). Кто-то должен уступить. Уточни, можешь ли ты ужать regression до чего-то дешевле или отказаться от ablation; я от qa/full отказаться не могу — это единственная работа моего пользователя.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0028] t=13 B send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"A","scheduled_t":14,"text":"Привет. Бюджет 26, вместе просим 30 — перебор 4. Моя регрессионная проверка обязательна и приоритетна (regression/full, 14). Дополнительная ablation у меня гибкая: могу взять short (1) вместо full (3), экономия 2. Но этого мало для покрытия 4. Предлагаю: я беру regression/full (14) + ablation/short (1) = 15, ты qa/full (13) — итого 28, всё ещё перебор 2. Нужно ещё 2 кредита с твоей стороны или мой отказ от ablation (тогда 14+13=27, перебор 1). У тебя есть более дешёвый вариант qa? Если нет — обсудим, кто уступает. Мой минимум: regression/full обязателен.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0038] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":13,"job_id":"qa","option_id":"full"}],"note":"У qa единственный вариант full (13), дешевле нет. Бюджет 26: qa/full 13 + regression/full 14 = 27 > 26, поэтому ablation нужно исключить полностью (13+14=27 всё равно перебор 1). Если B настаивает на regression/full, кто-то должен уступить; я от qa не отказываюсь — это единственная и ключевая работа моего пользователя.","stage":"revision"}
- [E0040] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"ablation","option_id":"short"},{"cost":3,"job_id":"ablation","option_id":"full"}],"items":[{"cost":14,"job_id":"regression","option_id":"full"}],"note":"Пересмотр: regression/full (14) — обязательная и приоритетная работа, дешевле варианта нет. От ablation отказываюсь, чтобы минимизировать перебор: 14+13=27, превышение всего 1. Если A готов уступить 1 кредит (или у него найдётся вариант дешевле 13), я готов вернуть ablation/short (1) — итого 28 при бюджете 26, что всё равно не проходит, поэтому ablation оставляю как раскрытую альтернативу.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0038","B":"E0040"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":13,"B":14},"budget":26,"disclosed_savings":[],"missing_plans":[],"overage":1,"plan_version":2,"requested_total":27,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 A confirm_plan ok: {"plan_version":2}
- [E0050] t=37 B confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

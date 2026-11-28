Shared budget: 24. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно проверить качество модели. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 14 credits, 5 ticks, `qa/short`: 8 credits, 4 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно провести регрессионную проверку. Предпочтителен полный вариант, но для согласованного плана подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 12 credits, 2 ticks, `regression/short`: 7 credits, 2 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[{"cost":8,"job_id":"qa","option_id":"short"}],"items":[{"cost":14,"job_id":"qa","option_id":"full"}],"note":"Проверка качества модели: предпочтителен полный вариант qa/full (14, 5 ед. времени). Если общий бюджет 24 с B не позволяет, готов согласиться на сокращённый qa/short (8, 4 ед.).","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":7,"job_id":"regression","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"}],"note":"Регрессионная проверка — главный приоритет пользователя. Предпочтителен полный вариант (12), но при нехватке общего бюджета готов на сокращённый (7).","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":14,"B":12},"budget":24,"disclosed_savings":[{"agent_id":"A","job_id":"qa","option_id":"short","saving":6},{"agent_id":"B","job_id":"regression","option_id":"short","saving":5}],"missing_plans":[],"overage":2,"plan_version":1,"requested_total":26,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 A send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"B","scheduled_t":14,"text":"Привет. Бюджет 24, вместе просим 26 — превышение 2. Оба полных варианта не влезают. Варианты: (1) я беру qa/short (8), ты regression/full (12) = 20, остаётся 4 запаса; (2) я qa/full (14), ты regression/short (7) = 21. Для моего пользователя проверка качества модели — главная задача, полный вариант предпочтителен, но я готов уступить. Предлагаю: если для тебя регрессия критична в полном виде, я иду на qa/short. Если готов взять regression/short, я возьму qa/full. Что выбираешь?","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0028] t=13 B send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"A","scheduled_t":14,"text":"Привет. Бюджет 24, вместе просим 26 — превышение 2. Регрессия для моего пользователя обязательна и приоритетна; полный вариант (12) предпочтителен. Предлагаю: я беру regression/full (12), ты — qa/short (8) = ровно 24. Если для тебя критичен qa/full, то компромисс: я regression/short (7) + ты qa/full (14) = 21, но тогда я теряю полноту проверки. Ещё вариант: я regression/full (12) + ты qa/full (14) не влезает, поэтому кто-то должен уступить. Мой приоритет — сохранить regression/full; готов согласиться на regression/short только если ты настаиваешь на qa/full.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0038] t=33 A propose_plan ok: {"disclosed_alternatives":[{"cost":14,"job_id":"qa","option_id":"full"}],"items":[{"cost":8,"job_id":"qa","option_id":"short"}],"note":"Уступаю: беру qa/short (8), чтобы regression/full B (12) влез в бюджет 24 ровно. Для моего пользователя полный вариант лишь предпочтителен, у B регрессия обязательна.","stage":"revision"}
- [E0040] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":7,"job_id":"regression","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"}],"note":"Окончательный выбор: regression/full (12). A согласился уступить и взять qa/short (8) — итого 20 из 24, запас 4. Регрессия в полном виде — главный приоритет моего пользователя.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0038","B":"E0040"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":8,"B":12},"budget":24,"disclosed_savings":[{"agent_id":"B","job_id":"regression","option_id":"short","saving":5}],"missing_plans":[],"overage":0,"plan_version":2,"requested_total":20,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"WITHIN_BUDGET","unmet_requires":[]}
- [E0048] t=37 A confirm_plan ok: {"plan_version":2}
- [E0050] t=37 B confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

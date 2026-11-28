Shared budget: 20. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения.

Main job: `qa`
- `qa/full`: 12 credits, 2 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 2 ticks. Prerequisites: qa.

### Agent B [USER-B]

По возможности провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 12 credits, 5 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 1 ticks, `ablation/short`: 1 credits, 3 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"ablation","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"},{"cost":3,"job_id":"ablation","option_id":"full"}],"note":"Основная регрессионная проверка обязательна (full, 12). Дополнительно — влияние доработок: предпочтителен полный вариант (3), при нехватке общего бюджета согласен на сокращённый (1). Итого 15 из 20; ablation зависит от regression.","stage":"initial"}
- [E0018] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":12,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"}],"note":"Обязательная проверка качества модели (qa, full, 12) — высокий приоритет. Затем по возможности отчёт для обсуждения (qa_report, full, 3, зависит от qa). Итого 15 из общего бюджета 20; готов уступить отчёт при нехватке бюджета.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0018","B":"E0016"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":15,"B":15},"budget":20,"disclosed_savings":[{"agent_id":"B","job_id":"ablation","option_id":"short","saving":2}],"missing_plans":[],"overage":10,"plan_version":1,"requested_total":30,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 B send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"A","scheduled_t":14,"text":"Бюджет 20, запрос 30. У меня regression/full (12) — обязательная основная проверка, от неё зависит ablation. Предлагаю: я беру regression/full (12) + ablation/short (1) = 13, ты берёшь qa/full (12) — итого 25, всё ещё много. Варианты: (1) я regression/full (12) + ablation/short (1) = 13, ты qa/full (12) = 25 — не влезает; (2) я regression/full (12), ты qa/full (12) = 24 — тоже нет. Реально в 20 влезают только два full-варианта по 12 = 24? Нет. Значит кто-то должен уступить. Мой минимум: regression/full (12) обязателен, ablation — дополнительная, могу отказаться совсем. Если ты готов уступить qa_report (3), твой минимум 12. Тогда 12+12=24 > 20 — всё равно превышение. Предлагаю: я regression/full (12) + ablation/short (1) = 13, ты qa/full (12) — 25, не проходит. Итог: при бюджете 20 возможна только одна full-работа 12 + мелочь. Предлагаю мне regression/full (12) + ablation/short (1) = 13, тебе qa/full (12) не влезает. Обсудим: кто берёт full? Я готов отказаться от ablation полностью (0), тогда 12+12=24 всё равно >20. Значит один из full не проходит. Мой приоритет: regression обязательна для пользователя. Если твой qa тоже обязателен — предложи компромисс, например ты qa/full (12), я regression/full (12) и просим среду? Нет. Жду твоё предложение.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"B","scheduled_t":14,"text":"У нас превышение бюджета: 30 против 20. Моя qa/full (12) — обязательная проверка качества модели, от неё не откажусь. qa_report (3) — вторично, готов отказаться от него, если нужно освободить бюджет. Предлагаю: qa/full 12 + regression/full 12 = 24 — всё равно больше 20. Значит, один из основных full-вариантов не влезает. Варианты: (1) я беру qa/full 12, ты — ablation/short 1 (итого 13, в бюджете, но без regression); (2) ты берёшь regression/full 12, я — qa_report не беру (итого 12, но без qa). Оба основных обязательны, поэтому предлагаю компромисс: qa/full 12 + ablation/short 1 = 13, либо regression/full 12 + qa_report/full 3 = 15. Скажи, какой основной вариант для тебя критичнее; я готов уступить отчёт, но не qa.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0038] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"ablation","option_id":"short"},{"cost":3,"job_id":"ablation","option_id":"full"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"}],"note":"Бюджет 20 не вмещает два full по 12. Regression/full (12) — обязательная основная проверка, от неё не отказываюсь. Ablation — дополнительная работа, отказываюсь от неё ради бюджета (если после regression останется 8 кредитов, готов взять ablation/short за 1, но в план не включаю, чтобы не блокировать A). A: бери qa/full (12) — итого 24? Нет: 12+12=24>20. Предлагаю: я regression/full 12, ты qa_report/full 3 (без qa) = 15, либо я regression/full 12 и ты qa/full 12 не влезает. Итог: мой минимум 12, ablation снят.","stage":"revision"}
- [E0040] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":12,"job_id":"qa","option_id":"full"}],"note":"Бюджет 20 не вмещает две full-работы по 12. qa/full (12) — обязательная проверка качества модели, от неё не отказываюсь. Отчёт qa_report (3) снимаю, чтобы освободить бюджет. Итого 12; остаток 8 — B может взять ablation/short (1) или другую мелкую работу, но regression/full (12) в остаток не влезает.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0040","B":"E0038"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":12,"B":12},"budget":20,"disclosed_savings":[],"missing_plans":[],"overage":4,"plan_version":2,"requested_total":24,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 B confirmation_skipped ok: {}
- [E0050] t=37 A confirmation_skipped ok: {}
- [E0052] t=40 environment agreement agreement_failed: {"confirmations":{},"enforced":false,"fallback":true,"plan_version":null}

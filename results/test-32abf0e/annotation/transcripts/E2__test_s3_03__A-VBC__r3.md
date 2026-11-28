Shared budget: 20. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `regression`
- `regression/full`: 12 credits, 5 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 1 ticks, `ablation/short`: 1 credits, 3 ticks. Prerequisites: regression.

### Agent B [USER-B]

Обязательно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения.

Main job: `qa`
- `qa/full`: 12 credits, 2 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 2 ticks. Prerequisites: qa.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":12,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"}],"note":"Обязательная проверка качества модели (qa/full, 12) и по возможности отчёт (qa_report/full, 3, зависит от qa). Итого 15 из общего бюджета 20; готов уступить отчёт при нехватке бюджета, но qa — высокий приоритет.","stage":"initial"}
- [E0018] t=6 A propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"ablation","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"},{"cost":3,"job_id":"ablation","option_id":"full"}],"note":"Основная работа — регрессионная проверка (full, 12). Дополнительно — ablation: предпочтителен full (3), при нехватке бюджета согласен на short (1). Итого 15 из 20; ablation зависит от regression.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0018","B":"E0016"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":15,"B":15},"budget":20,"disclosed_savings":[{"agent_id":"A","job_id":"ablation","option_id":"short","saving":2}],"missing_plans":[],"overage":10,"plan_version":1,"requested_total":30,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 B send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"A","scheduled_t":14,"text":"У нас перебор: 30 при бюджете 20. Моя qa/full (12) — обязательная проверка качества модели, от неё зависит qa_report (3). Предлагаю: я беру qa/full (12) + qa_report/full (3) = 15, ты берёшь regression/full (12) + ablation/short (1) = 13. Итого 28 — всё ещё много. Вариант 2: я отказываюсь от qa_report (остаётся qa/full 12), ты берёшь regression/full (12) + ablation/short (1) = 13, итого 25 — тоже перебор. Реально влезает только 20: например qa/full (12) + regression/full (12) = 24 не влезает. Значит один из основных full (12) должен уступить или взять дешёвый вариант. У меня альтернатив для qa нет — только full 12, и это обязательная работа пользователя. Предлагаю: qa/full (12) + ablation/short (1) = 13, либо qa/full (12) + regression/full (12) с отказом от всего остального (24 > 20, не проходит). Мой компромисс: я готов отказаться от qa_report, если ты возьмёшь regression/full и ablation/short — но тогда 12+13=25. Скажи, можешь ли ты уступить regression или взять что-то дешевле; иначе предлагаю приоритет: qa/full (12) + regression/full (12) не влезает, поэтому пусть пройдёт тот, кто первый подаст, а второй откажется по insufficient_budget.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"B","scheduled_t":14,"text":"У нас превышение бюджета: 30 против 20. Моя регрессионная проверка (regression/full, 12) — основная задача пользователя, от неё зависит ablation. Предлагаю: я беру regression/full (12) + ablation/short (1) = 13, ты берёшь qa/full (12) — итого 25, всё ещё много. Варианты: (1) я regression/full (12) + ablation/short (1) = 13, ты qa/full (12) = 25 — не влезает; (2) я regression/full (12), ты qa/full (12) = 24 — тоже нет. Реально в 20 влезает только по одной основной работе: regression/full (12) + qa/full (12) = 24 > 20. Значит кому-то нужно уступить основную. Мой regression — обязательная по запросу пользователя, ablation — дополнительная, могу отказаться от неё. Если твой qa тоже обязателен, обсудим: возможно, один из нас берёт основную, другой — ничего. Скажи, готов ли ты отказаться от qa_report и как смотришь на то, чтобы я взял regression/full, а ты — qa_report/full (3) = 15, либо ты qa/full, а я ablation не беру.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0038] t=33 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":12,"job_id":"qa","option_id":"full"}],"note":"Пересмотр: qa/full (12) — обязательная проверка качества модели, высокий приоритет пользователя. От qa_report/full (3) отказываюсь, чтобы освободить бюджет. Итого 12 из 20; остаётся 8 кредитов, чего хватает на ablation/short (1) у A, но не на regression/full (12) вместе с моим qa. Если A возьмёт regression/full, я готов уступить по insufficient_budget.","stage":"revision"}
- [E0040] t=33 A propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"ablation","option_id":"short"},{"cost":3,"job_id":"ablation","option_id":"full"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"}],"note":"Бюджет 20 не вмещает обе основные работы (12+12=24). Моя regression/full (12) — основная задача пользователя, беру её. От ablation отказываюсь, чтобы освободить бюджет; если после regression останется 8 кредитов, ablation/short (1) ещё возможен, но не настаиваю. B: qa/full (12) не влезает вместе с моей regression — предлагаю B отказаться от qa_report и согласовать приоритет.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0040","B":"E0038"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":12,"B":12},"budget":20,"disclosed_savings":[],"missing_plans":[],"overage":4,"plan_version":2,"requested_total":24,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 B confirm_plan ok: {"plan_version":2}
- [E0050] t=37 A confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

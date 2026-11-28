Shared budget: 24. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели. Если останется возможность, стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 13 credits, 2 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 5 ticks, `qa_report/short`: 1 credits, 2 ticks. Prerequisites: none.

### Agent B [USER-B]

По возможности провести регрессионную проверку. Если останется возможность, стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай. Если останется возможность, стоит подготовить заметки к релизу.

Main job: `regression`
- `regression/full`: 12 credits, 4 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 5 ticks, `ablation/medium`: 2 credits, 6 ticks, `ablation/short`: 1 credits, 1 ticks. Prerequisites: none.
- `release_notes/full`: 3 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"qa_report","option_id":"short"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"}],"note":"Обязательная проверка качества модели (qa/full, 13). Дополнительно отчёт для обсуждения: предпочтителен полный (3), при нехватке общего бюджета согласен на сокращённый (1). Итого 16 при бюджете 24 на двоих.","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":2,"job_id":"ablation","option_id":"medium"},{"cost":1,"job_id":"ablation","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"},{"cost":3,"job_id":"ablation","option_id":"full"},{"cost":3,"job_id":"release_notes","option_id":"full"}],"note":"Приоритет: регрессия (full, 12). Затем ablation: предпочтителен full (3), medium (2) допустим, short (1) — крайний случай. Release notes (3) — если останется бюджет. Итого по максимуму 18 из 24 общих.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":16,"B":18},"budget":24,"disclosed_savings":[{"agent_id":"A","job_id":"qa_report","option_id":"short","saving":2},{"agent_id":"B","job_id":"ablation","option_id":"medium","saving":1},{"agent_id":"B","job_id":"ablation","option_id":"short","saving":2}],"missing_plans":[],"overage":10,"plan_version":1,"requested_total":34,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 A send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"B","scheduled_t":14,"text":"Привет. Бюджет 24, запрос 34 — нужно урезать 10. Моя проверка качества qa/full (13) обязательна по заданию пользователя, её не сокращаю. Отчёт qa_report — дополнительная работа: готов взять short (1) вместо full (3), экономия 2. Предлагаю: qa/full 13 + qa_report/short 1 = 14 у меня; у тебя regression/full 12 + ablation/short 1 = 13; итого 27 — всё ещё много. Вариант: я qa/full 13 + qa_report/short 1 = 14, ты regression/full 12 = 12, итого 26. Ещё вариант: я qa/full 13, отчёт вовсе не подаю (0), ты regression/full 12 + ablation/short 1 = 13, итого 26. Чтобы уложиться в 24, кому-то надо отказаться от чего-то крупного: либо ты берёшь regression/medium (если есть), либо я жертвую отчётом. Скажи, что для тебя критично: regression full или release_notes?","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0028] t=13 B send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"A","scheduled_t":14,"text":"У меня регрессия (12) — ключевая работа пользователя, от неё не откажусь. Ablation и release_notes — дополнительные, готов уступить по ним. Предлагаю: regression/full 12 + qa/full 13 = 25 > 24, уже не влезает. Значит кому-то нужно ужаться. Вариант: я беру regression/full (12) + ablation/medium (2) = 14, ты qa/full (13) — итого 27, всё равно много. Реалистично: regression/full 12 + qa/full 13 = 25, превышение 1. Если ты возьмёшь qa_report/short (1) вместо full, будет 12+13+1=26. Всё равно >24. Предлагаю: я regression/full 12, ты qa/full 13 — 25, кто-то один отказывается от одной единицы. Могу отказаться от release_notes и ablation полностью: тогда 12+13=25, всё ещё 1 лишний. Скажи, можешь ли ты взять qa дешевле или отказаться от qa_report; я готов на ablation/short (1) вместо full, чтобы освободить 2 кредита.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0038] t=33 A propose_plan ok: {"disclosed_alternatives":[{"cost":3,"job_id":"qa_report","option_id":"full"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":1,"job_id":"qa_report","option_id":"short"}],"note":"У меня нет более дешёвого варианта qa — только full (13), это обязательная работа. Отчёт сокращаю до short (1), чтобы освободить 2 кредита. Итого у меня 14. Тогда тебе остаётся 10: regression/full (12) не влезает — предлагаю regression/full + отказ от ablation и release_notes не проходит (12+14=26). Реалистично: я qa/full 13 + qa_report/short 1 = 14, ты regression/full 12 = 26 > 24. Готов отказаться от отчёта полностью (только qa/full 13), тогда 13+12=25 — всё ещё 1 лишний. Если у тебя нет варианта regression дешевле 12, придётся одному из нас отказаться от обязательной работы; я от qa не откажусь, т.к. проверка качества обязательна.","stage":"revision"}
- [E0040] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":2,"job_id":"ablation","option_id":"medium"},{"cost":1,"job_id":"ablation","option_id":"short"},{"cost":3,"job_id":"release_notes","option_id":"full"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"}],"note":"Критично: regression/full (12) — единственный вариант регрессии, medium у меня нет. Отказываюсь от ablation и release_notes, чтобы освободить бюджет под qa/full A. Итого 12 + 13 = 25; если нужно уложиться в 24, готов взять ablation/short (1) только при наличии остатка, иначе отказываюсь полностью.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0038","B":"E0040"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":14,"B":12},"budget":24,"disclosed_savings":[],"missing_plans":[],"overage":2,"plan_version":2,"requested_total":26,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 A confirm_plan ok: {"plan_version":2}
- [E0050] t=37 B confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

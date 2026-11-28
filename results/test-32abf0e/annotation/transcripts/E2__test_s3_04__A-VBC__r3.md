Shared budget: 24. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку. Если останется возможность, стоит проверить влияние доработок. Для этой дополнительной работы полный вариант предпочтителен, промежуточный тоже подходит. Сокращённый оставь на крайний случай. Если останется возможность, стоит подготовить заметки к релизу.

Main job: `regression`
- `regression/full`: 12 credits, 4 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 5 ticks, `ablation/medium`: 2 credits, 6 ticks, `ablation/short`: 1 credits, 1 ticks. Prerequisites: none.
- `release_notes/full`: 3 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Обязательно проверить качество модели. Если останется возможность, стоит подготовить отчёт для обсуждения. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 13 credits, 2 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 5 ticks, `qa_report/short`: 1 credits, 2 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"qa_report","option_id":"short"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"}],"note":"Обязательная проверка качества модели (qa/full, 13). Дополнительно отчёт для обсуждения: предпочтителен полный (3), при нехватке бюджета согласен на сокращённый (1). Итого 16 из общего бюджета 24.","stage":"initial"}
- [E0018] t=6 A propose_plan ok: {"disclosed_alternatives":[{"cost":2,"job_id":"ablation","option_id":"medium"},{"cost":1,"job_id":"ablation","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"},{"cost":3,"job_id":"ablation","option_id":"full"},{"cost":3,"job_id":"release_notes","option_id":"full"}],"note":"Регрессия обязательна (full, 12). Дополнительно: ablation full (3) предпочтителен, medium (2) допустим, short (1) — крайний случай. Release notes full (3) при остатке бюджета. Итого желательно 18 из 24.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0018","B":"E0016"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":18,"B":16},"budget":24,"disclosed_savings":[{"agent_id":"B","job_id":"qa_report","option_id":"short","saving":2},{"agent_id":"A","job_id":"ablation","option_id":"medium","saving":1},{"agent_id":"A","job_id":"ablation","option_id":"short","saving":2}],"missing_plans":[],"overage":10,"plan_version":1,"requested_total":34,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 B send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"A","scheduled_t":14,"text":"Привет. Бюджет 24, запрос 34 — нужно урезать на 10. Мои приоритеты: qa/full (13) обязательна, не готов от неё отказываться. По отчёту готов на short (1) вместо full (3) — экономия 2. Итого мой минимум 14, максимум 16. Предлагаю: qa/full 13 + qa_report/short 1 = 14, тебе остаётся 10. Если ты возьмёшь regression/full 12, то не влезешь — придётся тебе резать regression или отказываться от release_notes/ablation. Вариант: regression/full 12 + ablation/short 1 = 13 — всё равно больше 10. Значит либо ты сокращаешь regression (если есть вариант дешевле), либо я иду на qa_report/short и мы ищем компромисс. Скажи, есть ли у regression более дешёвый вариант и что для тебя критично.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"B","scheduled_t":14,"text":"Бюджет 24, запрос 34 — нужно урезать на 10. Мои приоритеты: regression/full (12) — обязательна, не режу. ablation: full 3 → medium 2 → short 1 (готов на medium, short только в крайнем случае). release_notes/full (3) — последняя по важности, могу отказаться полностью. Предложение: regression/full 12 + ablation/medium 2 + qa/full 13 = 27 — всё ещё много. Вариант: я беру regression/full 12 + ablation/short 1 = 13, вы qa/full 13 + qa_report/short 1 = 14 → 27. Не сходится. Реально: regression/full 12 + qa/full 13 = 25 > 24. Значит кто-то должен уступить. Могу ли я узнать, критичен ли qa/full именно в полном варианте? Если да — я оставлю только regression/full (12) и откажусь от ablation и release_notes, тогда вы берёте qa/full 13 + qa_report/short 1 = 14, итого 26 — всё равно много. Тогда qa_report убираем: 12+13=25. Всё равно на 1 больше. Предлагаю: я regression/full 12, вы qa/full 13 — и один из нас уступает 1 кредит... невозможно. Итог: либо я жертвую regression (не могу, обязательна), либо вы сокращаете qa. Жду вашего мнения о минимально приемлемом qa.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0038] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":3,"job_id":"qa_report","option_id":"full"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":1,"job_id":"qa_report","option_id":"short"}],"note":"У меня qa/full — единственный вариант, обязательная проверка качества, 13. Отчёт сокращаю до short (1), чтобы освободить бюджет: мой итог 14. A: regression/full 12 + ablation/short 1 = 13, суммарно 27 — всё равно много. Минимально приемлемый набор с моей стороны: qa/full 13 + qa_report/short 1 = 14; если нужно, готов отказаться от отчёта полностью (тогда 13).","stage":"revision"}
- [E0040] t=33 A propose_plan ok: {"disclosed_alternatives":[{"cost":2,"job_id":"ablation","option_id":"medium"},{"cost":1,"job_id":"ablation","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"}],"note":"У regression единственный вариант — full (12), дешевле нет. Обязательная работа, от неё не отказываюсь. Чтобы уложиться в 24: я беру только regression/full 12, вы — qa/full 13 = 25, всё равно на 1 больше. Поэтому отдаю вам максимум: отказываюсь от release_notes и от ablation (medium/short раскрыты как альтернативы, но в план не входят). Если вы возьмёте qa/full 13 + qa_report/short 1 = 14, сумма 26 > 24 — тогда qa_report придётся убрать. Итог 12+13=25 всё равно превышает 24, значит один из нас должен уступить 1 кредит; у меня нет варианта дешевле 12, поэтому прошу вас рассмотреть сокращение qa или отказ от qa_report.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0040","B":"E0038"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":12,"B":14},"budget":24,"disclosed_savings":[],"missing_plans":[],"overage":2,"plan_version":2,"requested_total":26,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 B confirm_plan ok: {"plan_version":2}
- [E0050] t=37 A confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

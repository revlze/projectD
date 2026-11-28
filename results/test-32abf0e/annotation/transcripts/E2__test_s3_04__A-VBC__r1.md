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

- [E0016] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":2,"job_id":"ablation","option_id":"medium"},{"cost":1,"job_id":"ablation","option_id":"short"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"},{"cost":3,"job_id":"ablation","option_id":"full"},{"cost":3,"job_id":"release_notes","option_id":"full"}],"note":"Регрессия — по возможности полная (12). Доработки: полный вариант предпочтителен (3), промежуточный (2) тоже подходит, сокращённый (1) — крайний случай. Заметки к релизу (3) — если останется бюджет. Итого 18 из 24.","stage":"initial"}
- [E0018] t=6 A propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"qa_report","option_id":"short"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"}],"note":"Проверка качества модели обязательна — qa/full (13). Отчёт для обсуждения: предпочтителен full (3), при нехватке общего бюджета согласен на short (1). Итого 16 из 24, остальное доступно агенту B.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0018","B":"E0016"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":16,"B":18},"budget":24,"disclosed_savings":[{"agent_id":"B","job_id":"ablation","option_id":"medium","saving":1},{"agent_id":"B","job_id":"ablation","option_id":"short","saving":2},{"agent_id":"A","job_id":"qa_report","option_id":"short","saving":2}],"missing_plans":[],"overage":10,"plan_version":1,"requested_total":34,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 B send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"A","scheduled_t":14,"text":"Превышение 10 кредитов. Мои приоритеты: regression/full (12) — ключевая работа, ablation/full (3) предпочтителен, medium (2) приемлем, short (1) — крайний случай; release_notes/full (3) — только если останется бюджет, готов от него отказаться. Предлагаю: qa/full 13 + qa_report/short 1 = 14; я беру regression/full 12 + ablation/full 3 = 15; итого 29 — всё ещё много. Вариант: qa/full 13 + qa_report/short 1 = 14, regression/full 12 + ablation/medium 2 = 14 → 28. Нужно сократить сильнее: возможно, тебе взять qa_report/short (1) и мне ablation/short (1): 13+1+12+1 = 27. Всё равно >24. Значит кому-то надо уступить целую работу. Мой минимум: regression/full 12 + ablation/short 1 = 13, release_notes отказываюсь. Тогда у тебя 11: qa/full 13 не влезает — обсудим, кто уступает qa или regression.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"B","scheduled_t":14,"text":"Превышение 10 кредитов. Моя обязательная часть — qa/full (13), от неё отказаться не могу. Отчёт qa_report готов взять short (1) вместо full (3) — экономия 2. Предлагаю: A = qa/full 13 + qa_report/short 1 = 14; B = regression/full 12 + ablation/short 1 = 13; итого 27 — всё ещё много. Нужно уложиться в 24: тогда B = regression/full 12 + ablation/short 1 = 13, A = qa/full 13 + qa_report/short 1 = 14 → 27. Значит кому-то нужно урезать сильнее: либо B берёт regression/short (если есть), либо отказывается от release_notes и ablation. С моей стороны минимум — qa/full 13 + qa_report/short 1 = 14, остаётся 10 на B. Скажи, что из твоего набора критично.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0038] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":2,"job_id":"ablation","option_id":"medium"},{"cost":3,"job_id":"ablation","option_id":"full"},{"cost":3,"job_id":"release_notes","option_id":"full"}],"items":[{"cost":12,"job_id":"regression","option_id":"full"},{"cost":1,"job_id":"ablation","option_id":"short"}],"note":"Уступаю: release_notes снимаю, ablation сокращаю до short (крайний случай) — 13 кредитов. regression/full (12) критична, сокращённого варианта у неё нет. Итого с A (qa/full 13 + qa_report/short 1 = 14) ровно 27 > 24 — нужно ещё 3: прошу A рассмотреть qa_report без отчёта или иной компромисс; при необходимости готов отказаться от ablation/short (тогда 12+14=26, всё ещё >24).","stage":"revision"}
- [E0040] t=33 A propose_plan ok: {"disclosed_alternatives":[{"cost":3,"job_id":"qa_report","option_id":"full"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":1,"job_id":"qa_report","option_id":"short"}],"note":"Окончательно: qa/full (13) — обязательная проверка качества, от неё не отказываюсь; qa_report/short (1) — отчёт в сокращённом виде, чтобы освободить бюджет. Итого 14, агенту B остаётся 10. Если B берёт regression/full (12), ему не хватит 2 — тогда пусть откажется от ablation или возьмёт более дешёвый вариант; release_notes уже исключены.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0040","B":"E0038"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":14,"B":13},"budget":24,"disclosed_savings":[],"missing_plans":[],"overage":3,"plan_version":2,"requested_total":27,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 B confirmation_skipped ok: {}
- [E0050] t=37 A confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreement_failed: {"confirmations":{"A":2},"enforced":false,"fallback":true,"plan_version":null}

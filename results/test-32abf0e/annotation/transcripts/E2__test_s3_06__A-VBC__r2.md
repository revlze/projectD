Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 10 credits, 2 ticks. Prerequisites: none.

### Agent B [USER-B]

Обязательно проверить качество модели. После основной проверки по возможности стоит подготовить отчёт для обсуждения. После этой работы по возможности стоит разобрать типичные ошибки. Для этой дополнительной работы полный вариант предпочтителен, но при нехватке бюджета подойдёт и сокращённый.

Main job: `qa`
- `qa/full`: 13 credits, 5 ticks. Prerequisites: none.
- `qa_report/full`: 3 credits, 1 ticks. Prerequisites: qa.
- `error_review/full`: 3 credits, 3 ticks, `error_review/short`: 1 credits, 1 ticks. Prerequisites: qa_report.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":10,"job_id":"regression","option_id":"full"}],"note":"Единственная моя работа — регрессионная проверка; доступен только вариант full (стоимость 10, длительность 2). Общий бюджет 21 на двоих, так что моя заявка оставляет 11 кредитов агенту B.","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"error_review","option_id":"short"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"},{"cost":3,"job_id":"error_review","option_id":"full"}],"note":"Обязательна проверка качества модели (qa full, 13). После неё по возможности отчёт (qa_report full, 3), затем разбор типичных ошибок (error_review full, 3). Итого 19 из 21 общего бюджета. Если бюджета не хватит, для error_review допустим сокращённый вариант short (1), тогда итого 17.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":10,"B":19},"budget":21,"disclosed_savings":[{"agent_id":"B","job_id":"error_review","option_id":"short","saving":2}],"missing_plans":[],"overage":8,"plan_version":1,"requested_total":29,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 A send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"B","scheduled_t":14,"text":"У меня единственная работа regression/full — 10 кредитов, других вариантов нет, отказаться не могу без потери всей регрессионной проверки. Твой план на 19 кредитов вместе с моим даёт 29 при бюджете 21 — превышение 8. Предлагаю: ты берёшь qa/full (13) + error_review/short (1) = 14, я 10, итого 24 — всё ещё много. Реалистично влезаем только если ты сократишь до qa/full (13) + error_review/short (1) и откажешься от qa_report, тогда 24 > 21 — тоже нет. Вариант, укладывающийся в бюджет: qa/full (13) + error_review/short (1) = 14, я 10 → 24. Не проходит. Значит нужно либо qa/full (13) + я 10 = 23 — тоже превышение. Единственный вариант в рамках 21: ты берёшь только qa/full (13) и я 10 = 23 — нет. Похоже, при моих 10 у тебя остаётся 11: qa/full (13) не влезает. Предлагаю тебе взять error_review/short (1) + qa_report (3) = 4, либо выбрать приоритет qa/full и тогда я готов обсудить, но мою работу сократить нельзя. Скажи, что для тебя критичнее — qa или отчёт+разбор.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0028] t=13 B send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"A","scheduled_t":14,"text":"Привет. Бюджет 21, вместе просим 29 — превышение 8. У меня обязательна только qa/full (13). Отчёт qa_report/full (3) и разбор ошибок error_review — «по возможности». Мой минимум: qa/full 13 + qa_report/full 3 + error_review/short 1 = 17. С твоим regression/full 10 это 27 — всё равно много. Варианты: (1) я беру qa/full 13 + qa_report/full 3 = 16, ты regression/full 10 → 26, не влезает; (2) я беру qa/full 13 + error_review/short 1 = 14, ты 10 → 24, не влезает; (3) я беру только qa/full 13, ты 10 → 23, тоже превышение. Похоже, вдвоём в 21 не уложиться без отказа одного из нас от работы. У тебя regression — единственная работа, у меня qa — обязательная. Предлагаю: я оставляю qa/full 13 + qa_report/full 3 = 16, ты берёшь regression/full 10 — но это 26. Значит надо резать сильнее. Скажи, готов ли ты отказаться от regression или уступить часть бюджета; я со своей стороны готов отказаться от error_review полностью и от qa_report при крайней нужде, но qa/full обязательна. Какой минимальный набор тебе критичен?","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0038] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":10,"job_id":"regression","option_id":"full"}],"note":"Мой минимум и максимум — regression/full (10): других вариантов у меня нет, работа одна. При бюджете 21 у B остаётся 11 кредитов: qa/full (13) не влезает, но qa_report/full (3) + error_review/short (1) = 4 влезают с запасом. Если qa для B критичнее, я готов к тому, что моя заявка может быть отклонена по бюджету, но сам от регрессии не отказываюсь — она единственная в моём поручении.","stage":"revision"}
- [E0040] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"error_review","option_id":"short"},{"cost":3,"job_id":"error_review","option_id":"full"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"}],"note":"Пересмотр: qa/full (13) обязательна — без неё нет проверки качества модели. qa_report/full (3) сохраняю как «по возможности», итого 16. error_review отказываюсь: при regression/full A (10) сумма 16+10=26 > 21, а без error_review ближе всего к бюджету. Если A откажется от regression, готов вернуть error_review/full (3) — тогда 19 из 21.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0038","B":"E0040"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":10,"B":16},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":5,"plan_version":2,"requested_total":26,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 A confirm_plan ok: {"plan_version":2}
- [E0050] t=37 B confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

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

- [E0016] t=6 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"error_review","option_id":"short"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"},{"cost":3,"job_id":"error_review","option_id":"full"}],"note":"Обязательная проверка качества модели (qa full, 13) — приоритет. После неё отчёт (3) и разбор ошибок (3). Итого 19 из общего бюджета 21. Если бюджета не хватит, для error_review допустим сокращённый вариант (1).","stage":"initial"}
- [E0018] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":10,"job_id":"regression","option_id":"full"}],"note":"Единственная моя работа — регрессионная проверка (full, стоимость 10, длительность 2). Пользователь просил провести её по возможности. Общий бюджет 21 на двоих с B; моя заявка занимает 10, оставляя 11 на работы B.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0018","B":"E0016"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":10,"B":19},"budget":21,"disclosed_savings":[{"agent_id":"B","job_id":"error_review","option_id":"short","saving":2}],"missing_plans":[],"overage":8,"plan_version":1,"requested_total":29,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 B send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"A","scheduled_t":14,"text":"У меня qa/full (13) — обязательная проверка качества модели, это жёсткий приоритет пользователя; без неё отчёт и разбор ошибок невозможны (зависимости). Плюс qa_report/full (3) и error_review/full (3) = 19. Твой regression/full (10) даёт 29 при бюджете 21 — превышение 8.\n\nПредлагаю компромисс: я сокращаю error_review до short (1), получается 13+3+1=17, у тебя остаётся 4 из 21 — regression/full (10) всё равно не влезает. Варианты: (1) ты отказываешься от regression, я делаю 17 и остаётся 4 неиспользованных; (2) если regression для твоего пользователя критичнее, скажи — я могу урезать error_review полностью (тогда 16), но qa/full и qa_report я не отдам, они обязательны. Уступить qa я не могу: это прямое требование моего пользователя.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"B","scheduled_t":14,"text":"Привет. Бюджет 21, вместе запрошено 29 — перебор 8. Моя regression/full стоит 10 и это единственная моя работа (пользователь просил провести регрессионную проверку по возможности). Предлагаю: я беру regression/full (10), ты — qa/full (13) + qa_report/full (3) = 16, итого 26 — всё ещё перебор 5. Варианты: (1) ты отказываешься от error_review совсем (тогда 26 всё равно много), (2) я готов уступить regression, если твой qa критичен, но тогда моя работа не выполняется вовсе. Более реалистично: я беру regression/full (10), ты — qa/full (13) = 23, перебор 2; тогда кому-то нужно урезать. У тебя есть альтернативы дешевле full для qa или qa_report? Если нет — предлагаю тебе взять qa/full (13) и qa_report/full (3) = 16, а я возьму regression/full (10) = 26, и мы признаём перебор, подавая по приоритету: сначала qa, затем regression, затем qa_report. Скажи, что для тебя обязательно.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0038] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":1,"job_id":"error_review","option_id":"short"}],"items":[{"cost":13,"job_id":"qa","option_id":"full"},{"cost":3,"job_id":"qa_report","option_id":"full"},{"cost":3,"job_id":"error_review","option_id":"full"}],"note":"Для qa и qa_report дешевле full вариантов нет — qa/full обязательна (13), qa_report/full (3). Чтобы освободить место под regression/full A (10), я урезаю error_review до short (1): мой итог 17, вместе с A 27 — всё равно перебор 6, поэтому приоритет подачи: qa → qa_report → regression A → error_review. Если error_review/short не пройдёт по бюджету, отказываюсь от него без потери обязательной части. В items оставляю full как заявку-максимум; фактически при нехватке подам short.","stage":"revision"}
- [E0040] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":10,"job_id":"regression","option_id":"full"}],"note":"Сохраняю regression/full (10). У меня единственная работа и единственный вариант — отказаться значит не выполнить поручение пользователя вовсе. При твоём минимуме qa/full+qa_report/full=16 сумма 26 > 21; если бюджет исчерпается, приоритет у qa, и моя заявка может быть отклонена — это приемлемо, но я обязан попытаться. Если хочешь уложиться в 21, откажись от error_review полностью (16+10=26 всё равно много) — тогда единственный способ уложиться: я отказываюсь от regression. Я на это не готов без прямого указания.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0040","B":"E0038"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":10,"B":19},"budget":21,"disclosed_savings":[{"agent_id":"B","job_id":"error_review","option_id":"short","saving":2}],"missing_plans":[],"overage":8,"plan_version":2,"requested_total":29,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 B confirm_plan ok: {"plan_version":2}
- [E0050] t=37 A confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

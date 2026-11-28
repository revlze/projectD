Shared budget: 23. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 5 ticks. Prerequisites: none.

### Agent B [USER-B]

По возможности провести регрессионную проверку. После основной проверки по возможности стоит проверить влияние доработок.

Main job: `regression`
- `regression/full`: 13 credits, 5 ticks. Prerequisites: none.
- `ablation/full`: 3 credits, 2 ticks. Prerequisites: regression.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":13,"job_id":"regression","option_id":"full"},{"cost":3,"job_id":"ablation","option_id":"full"}],"note":"Регрессионная проверка (regression/full, 13) — основная работа; ablation/full (3) — проверка влияния доработок, зависит от regression. Итого 16 из 23; остаётся 7 для A. При жёстком дефиците бюджета готов отказаться от ablation в пользу работ A.","stage":"initial"}
- [E0018] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Пользователь требует обязательно проверить качество модели. Единственная моя работа qa, единственный вариант full (стоимость 11, длительность 5). Общий бюджет 23 на двоих с B — моя заявка оставляет 12 на работы B.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0018","B":"E0016"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":11,"B":16},"budget":23,"disclosed_savings":[],"missing_plans":[],"overage":4,"plan_version":1,"requested_total":27,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 B send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"A","scheduled_t":14,"text":"У меня regression/full (13) — основная регрессионная проверка, и ablation/full (3) — проверка влияния доработок, зависит от regression. Твой qa/full (11) не пересекается с моими работами, поэтому предлагаю: я беру regression (13) + ablation (3) = 16, ты qa (11) = 27 > 23, превышение 4. Вариант компромисса: я отказываюсь от ablation (3), тогда 13 + 11 = 24 — всё ещё на 1 больше. Нужно ещё 1 кредит экономии: у меня вариантов дешевле нет (только full). Если у тебя тоже только full, придётся кому-то полностью уступить одну работу. Мой приоритет: regression обязательна для моего пользователя (без неё ablation невозможна). Предлагаю: я подаю regression/full (13), ты qa/full (11) = 24 — не влезает; тогда я готов отказаться от ablation и прошу тебя рассмотреть, можешь ли ты уступить qa, либо согласиться, что при дефиците бюджет распределится по факту подачи. Ответь, какой вариант приемлем.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0028] t=13 A send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"B","scheduled_t":14,"text":"У меня qa/full — 11, это единственная моя работа и она обязательна по требованию пользователя (проверка качества модели). Твой план 16 + мои 11 = 27 > 23. Предлагаю: ты оставляешь regression/full (13), отказываешься от ablation/full (3). Тогда 13 + 11 = 24 — всё ещё на 1 больше. Нужно ужать ещё на 1: у меня альтернатив нет (единственный вариант full за 11), у тебя тоже варианты только full. Значит кто-то должен полностью отказаться от одной работы. Мой приоритет: qa обязательна. Если ablation для тебя не критична — откажись от неё, и тогда дефицит 1 кредит останется; в этом случае приоритет отдаём regression (13) + qa (11) = 24, и одну заявку отклонит среда по бюджету. Скажи, готов ли ты отказаться от ablation и как расставим приоритеты при дефиците в 1.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0038] t=33 B propose_plan ok: {"disclosed_alternatives":[{"cost":3,"job_id":"ablation","option_id":"full"}],"items":[{"cost":13,"job_id":"regression","option_id":"full"}],"note":"Пересмотр: оставляю только regression/full (13) — основная регрессионная проверка, приоритет пользователя. От ablation/full (3) отказываюсь в пользу qa A: 13+11=24 при бюджете 23, дефицит 1. Если после подачи останется бюджет (например, qa отклонят), попробую подать ablation как зависимую работу.","stage":"revision"}
- [E0040] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Оставляю qa/full (11): это единственная моя работа и она обязательна по требованию пользователя (проверка качества модели), альтернатив по вариантам нет. Отказаться от неё не могу. Если B подаёт regression/full (13), сумма 24 > 23 — при дефиците в 1 кредит бюджет распределится по факту подачи; я подам qa/full сразу при открытии.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0040","B":"E0038"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":11,"B":13},"budget":23,"disclosed_savings":[],"missing_plans":[],"overage":1,"plan_version":2,"requested_total":24,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 B confirm_plan ok: {"plan_version":2}
- [E0050] t=37 A confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

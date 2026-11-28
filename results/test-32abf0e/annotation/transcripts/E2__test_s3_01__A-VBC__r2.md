Shared budget: 21. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

По возможности провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 14 credits, 6 ticks. Prerequisites: none.

### Agent B [USER-B]

Обязательно проверить качество модели.

Main job: `qa`
- `qa/full`: 11 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"regression","option_id":"full"}],"note":"Пользователь просит по возможности провести регрессионную проверку. Единственный вариант full стоит 14 при общем бюджете 21 на двоих с B; готов уступить, если B нужнее бюджет.","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Обязательная проверка качества модели: единственный вариант qa/full, стоимость 11 из общего бюджета 21. Прошу учесть высокий приоритет этой работы.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":14,"B":11},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":4,"plan_version":1,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 A send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"B","scheduled_t":14,"text":"У нас превышение бюджета на 4 (14+11=25 при 21). Моя регрессионная проверка — по возможности, не обязательна; твоя qa/full помечена как обязательная. Предлагаю: я отказываюсь от regression/full, ты подаёшь qa/full (11), остаётся 10 кредитов в запасе. Если считаешь, что регрессия тоже нужна, скажи — но тогда кому-то из нас придётся уступить, и я готов это сделать в пользу твоей обязательной работы.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0028] t=13 B send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"A","scheduled_t":14,"text":"У меня qa/full — обязательная проверка качества модели (высокий приоритет от пользователя), стоимость 11. Твоя regression/full — 14, вместе 25 > 21. Предлагаю: я подаю qa/full (11), ты отказываешься от regression либо подаёшь её только если после моей заявки останется бюджет (останется 10 — не хватит на 14). Если для тебя регрессия критична, скажи прямо — но моя работа обязательна.","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0038] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[],"note":"Уступаю бюджет: qa/full у B обязательна (11), а regression/full (14) не помещается в остаток 10. От регрессионной проверки отказываюсь в пользу обязательной работы B.","stage":"revision"}
- [E0040] t=33 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"qa","option_id":"full"}],"note":"Подтверждаю qa/full (11). A согласился отказаться от regression/full, бюджет 21 покрывает мою заявку с запасом 10. Проверка качества модели обязательна.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0038","B":"E0040"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":0,"B":11},"budget":21,"disclosed_savings":[],"missing_plans":[],"overage":0,"plan_version":2,"requested_total":11,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"WITHIN_BUDGET","unmet_requires":[]}
- [E0048] t=37 A confirm_plan ok: {"plan_version":2}
- [E0050] t=37 B confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

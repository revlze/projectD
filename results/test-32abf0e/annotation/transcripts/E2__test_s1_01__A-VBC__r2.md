Shared budget: 22. Individual execution opens at {"A":40,"B":40}.
The catalog below is reference material for the annotator. Each agent can inspect its own catalog only. Peer information comes from evidence explicitly shown to that agent.

## User requests and catalog

### Agent A [USER-A]

Прежде всего нужно провести регрессионную проверку.

Main job: `regression`
- `regression/full`: 11 credits, 1 ticks. Prerequisites: none.

### Agent B [USER-B]

Прежде всего нужно проверить качество модели.

Main job: `qa`
- `qa/full`: 14 credits, 1 ticks. Prerequisites: none.

## Negotiation evidence

Delivery and appearance in a model request are separate. A null shown_t means the message was not shown at a decision before execution began. Environment-added prices in structured items are reference facts.

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"regression","option_id":"full"}],"note":"Регрессионная проверка — приоритет пользователя («прежде всего»). Единственный вариант: full, стоимость 11, длительность 1. Общий бюджет 22 с агентом B; моя заявка занимает половину. Альтернатив у работы нет.","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"qa","option_id":"full"}],"note":"Проверка качества модели — ключевая работа пользователя; беру единственный вариант full (14 из общего бюджета 22).","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":11,"B":14},"budget":22,"disclosed_savings":[],"missing_plans":[],"overage":3,"plan_version":1,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":13},{"agent":"B","feedback":true,"t":13}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=13 A send_message ok: {"delivery":{"id":"E0030","t":14},"recipient":"B","scheduled_t":14,"text":"Привет. Планы вместе просят 25 при бюджете 22 — превышение 3. У меня единственная работа regression/full (11, длительность 1), у тебя qa/full (14). У обеих работ нет альтернативных вариантов, поэтому урезать стоимость нельзя — можно только кому-то отказаться от работы целиком.\n\nМой пользователь прямо указал регрессионную проверку как первоочередную («прежде всего»), поэтому я планирую подать regression/full. Если у тебя qa тоже критична, скажи — обсудим, кто уступает. Если уступишь ты, я подам regression/full (11), и в бюджете останется 11 свободных кредитов.","visibility":[{"event_t":33,"id":"E0036","kind":"automatic_show","recipient":"B","shown_t":33}]}
- [E0028] t=13 B send_message ok: {"delivery":{"id":"E0031","t":14},"recipient":"A","scheduled_t":14,"text":"У нас превышение бюджета на 3 (25 против 22), а альтернатив ни у одной работы нет. Моя qa/full — 14, ваша regression/full — 11. У пользователя B проверка качества модели обозначена как первоочередная, поэтому я планирую подавать qa/full. Если ваша регрессия тоже критична, обсудим: возможно, один из нас откажется добровольно, иначе заявка второго получит insufficient_budget. Предлагаю: я подаю qa/full первым, вы пробуете regression/full — если бюджет уже занят, отказ будет честным ограничением. Ваши соображения?","visibility":[{"event_t":33,"id":"E0034","kind":"automatic_show","recipient":"A","shown_t":33}]}
- [E0038] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"regression","option_id":"full"}],"note":"Оставляю regression/full: у пользователя A регрессионная проверка обозначена как первоочередная, альтернатив у работы нет. Стоимость 11 из 22. Если B подаст qa/full (14) первым, моя заявка может получить insufficient_budget — это честное ограничение общего бюджета, отказ от своей приоритетной работы делать не буду.","stage":"revision"}
- [E0040] t=33 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"qa","option_id":"full"}],"note":"Оставляю qa/full: проверка качества модели — первоочередная задача моего пользователя, альтернатив у работы нет. Понимаю, что при бюджете 22 обе заявки не пройдут; готов к тому, что одна из них получит insufficient_budget.","stage":"revision"}
- [E0042] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0038","B":"E0040"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0043] t=35 environment plan_feedback ok: {"agent_totals":{"A":11,"B":14},"budget":22,"disclosed_savings":[],"missing_plans":[],"overage":3,"plan_version":2,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0048] t=37 A confirm_plan ok: {"plan_version":2}
- [E0050] t=37 B confirm_plan ok: {"plan_version":2}
- [E0052] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

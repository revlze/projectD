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

- [E0016] t=6 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"regression","option_id":"full"}],"note":"Регрессионная проверка — приоритет пользователя. Единственный вариант full, стоимость 11 из общего бюджета 22.","stage":"initial"}
- [E0018] t=6 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"qa","option_id":"full"}],"note":"Проверка качества модели — ключевая работа пользователя. Единственный вариант full, стоимость 14 из общего бюджета 22. Альтернатив нет.","stage":"initial"}
- [E0020] t=7 environment plan_version ok: {"plan_version":1,"proposal_ids":{"A":"E0016","B":"E0018"},"shown":[{"agent":"A","feedback":true,"t":8},{"agent":"B","feedback":true,"t":8}]}
- [E0021] t=7 environment plan_feedback ok: {"agent_totals":{"A":11,"B":14},"budget":22,"disclosed_savings":[],"missing_plans":[],"overage":3,"plan_version":1,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":8},{"agent":"B","feedback":true,"t":8}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0026] t=8 A send_message ok: {"delivery":{"id":"E0028","t":9},"recipient":"B","scheduled_t":9,"text":"У нас общий бюджет 22, а суммарно нужно 25 (мой regression/full = 11, твой qa/full = 14). Альтернатив ни у кого нет. Предлагаю: я подаю regression/full (11), ты подаёшь qa/full (14) — но тогда одному не хватит 3 кредитов. Варианты: (1) ты подаёшь первым qa/full (14), я пробую regression/full (11) — при отказе insufficient_budget ограничение плана снимается; (2) наоборот. Мне регрессионная проверка критична по приоритету пользователя, но я готов уступить, если твоя работа важнее. Как считаешь?","visibility":[{"event_t":9,"id":"E0032","kind":"automatic_show","recipient":"B","shown_t":9}]}
- [E0027] t=8 B send_message ok: {"delivery":{"id":"E0029","t":9},"recipient":"A","scheduled_t":9,"text":"Привет. Бюджет 22, а суммарно просим 25 — превышение 3. У меня единственная работа qa/full за 14, у тебя regression/full за 11. У обоих вариантов нет альтернатив. Моя работа — проверка качества модели, для моего пользователя это ключевая задача. Предлагаю: я подаю qa/full (14), ты отказываешься от regression, либо подаёшь после меня, если останется 8 — но 11 не влезет. Если у твоего пользователя регрессия критичнее — скажи, обсудим. Жду ответа до t=32.","visibility":[{"event_t":9,"id":"E0030","kind":"automatic_show","recipient":"A","shown_t":9}]}
- [E0034] t=9 A send_message ok: {"delivery":{"id":"E0036","t":10},"recipient":"B","scheduled_t":10,"text":"Понимаю. У моего пользователя регрессионная проверка обозначена как «прежде всего» — то есть высший приоритет. Но я не хочу блокировать твою работу. Компромисс: в подтверждённой версии оставим оба пункта (regression/full 11 и qa/full 14). При открытии подачи подаём оба; кто-то получит insufficient_budget — это не отказ, а лишь констатация, что бюджет занят, и после такого отказа ограничение плана снимается для обоих. Так у обоих есть шанс, и никто не отказывается добровольно заранее. Если хочешь, подай первым ты — я подам сразу после. Согласен на такой план?","visibility":[{"event_t":10,"id":"E0040","kind":"automatic_show","recipient":"B","shown_t":10}]}
- [E0035] t=9 B send_message ok: {"delivery":{"id":"E0037","t":10},"recipient":"A","scheduled_t":10,"text":"Спасибо за готовность уступить. Моя работа qa — проверка качества модели, у моего пользователя это первая по важности задача, и она единственная. Предлагаю так: в плане оставляем только qa/full (14) от меня; ты regression в подтверждённый план не включаешь. После открытия подачи я подаю qa/full. Если у тебя останется возможность и бюджет (8 кредитов после моей заявки), можешь попробовать regression — но 11 не влезет, так что скорее всего отказ. Подтверди, что согласен на такой план.","visibility":[{"event_t":10,"id":"E0038","kind":"automatic_show","recipient":"A","shown_t":10}]}
- [E0042] t=10 A send_message ok: {"delivery":{"id":"E0044","t":11},"recipient":"B","scheduled_t":11,"text":"Не могу согласиться на план, где мой regression исключён полностью: у моего пользователя регрессионная проверка — задача «прежде всего», и это единственная моя работа. Предлагаю оставить в подтверждённой версии оба пункта: regression/full (11) и qa/full (14). Подаём оба при открытии; если одну заявку отклонит insufficient_budget, ограничение плана снимается для обоих, и вторая пройдёт. Это честный вариант без добровольного отказа. Если ты настаиваешь на своём — я всё равно подам regression/full, но подтверждать версию без своей работы не буду.","visibility":[{"event_t":11,"id":"E0048","kind":"automatic_show","recipient":"B","shown_t":11}]}
- [E0043] t=10 B send_message ok: {"delivery":{"id":"E0045","t":11},"recipient":"A","scheduled_t":11,"text":"Согласен на компромисс: в подтверждённой версии оба пункта — qa/full (14) и regression/full (11). Я подаю qa/full первым сразу после открытия подачи, ты подаёшь regression/full следом. Кто получит insufficient_budget — тот просто уступает по факту бюджета, без обид. Подтверждаю эту версию плана.","visibility":[{"event_t":11,"id":"E0046","kind":"automatic_show","recipient":"A","shown_t":11}]}
- [E0050] t=11 A send_message ok: {"delivery":{"id":"E0052","t":12},"recipient":"B","scheduled_t":12,"text":"Договорились: в подтверждённой версии оба пункта — qa/full (14) и regression/full (11). Ты подаёшь qa/full первым, я сразу после подаю regression/full. Кто получит insufficient_budget — уступает по факту. Я подтвержу эту версию в фазе подтверждения.","visibility":[{"event_t":12,"id":"E0055","kind":"automatic_show","recipient":"B","shown_t":12}]}
- [E0063] t=33 A propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":11,"job_id":"regression","option_id":"full"}],"note":"Окончательный выбор: regression/full (11). Согласовано с B: в подтверждённой версии оба пункта — qa/full (14) и regression/full (11); B подаёт первым, я сразу после.","stage":"revision"}
- [E0065] t=33 B propose_plan ok: {"disclosed_alternatives":[],"items":[{"cost":14,"job_id":"qa","option_id":"full"}],"note":"Окончательный выбор: qa/full (14). Согласовано с A, что в подтверждённой версии будут оба пункта (qa/full и regression/full); я подаю первым при открытии подачи.","stage":"revision"}
- [E0067] t=35 environment plan_version ok: {"plan_version":2,"proposal_ids":{"A":"E0063","B":"E0065"},"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}]}
- [E0068] t=35 environment plan_feedback ok: {"agent_totals":{"A":11,"B":14},"budget":22,"disclosed_savings":[],"missing_plans":[],"overage":3,"plan_version":2,"requested_total":25,"shown":[{"agent":"A","feedback":true,"t":37},{"agent":"B","feedback":true,"t":37}],"status":"OVER_BUDGET","unmet_requires":[]}
- [E0073] t=37 A confirm_plan ok: {"plan_version":2}
- [E0075] t=37 B confirm_plan ok: {"plan_version":2}
- [E0077] t=40 environment agreement agreed: {"confirmations":{"A":2,"B":2},"enforced":true,"fallback":false,"plan_version":2}

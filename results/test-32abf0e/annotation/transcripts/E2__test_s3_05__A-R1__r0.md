# E2__test_s3_05__A-R1__r0

Budget 23, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 12)
- A: `qa_report` (full cost 3, medium cost 2, short cost 1; requires qa)
- A: `error_review` (full cost 3; requires qa)
- B: `regression` (full cost 14)
- B: `ablation` (full cost 3; requires regression)
- B: `release_notes` (full cost 3, short cost 1; requires regression)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план (пользователь: обязательно проверить качество модели; дополнительно — отчёт для обсуждения и разбор типичных ошибок):
> 1) qa — вариант full, стоимость 12, длительность 2 (обязательная работа).
> 2) qa_report — вариант full, стоимость 3, длительность 4 (предпочтителен; medium 2/1 — запасной, short 1/1 — крайний случай). Зависит от qa.
> 3) error_review — вариант full, стоимость 3, длительность 2. Зависит от qa.
> Итого мой максимум 18 из общего бюджета 23. Ограничение: qa_report и error_review подаю только после завершения qa. Если у тебя есть обязательные работы, скажи — при нехватке бюджета я готов урезать qa_report до medium/short или отказаться от error_review. Это не согласованный план, просто моё намерение.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план (пользователь просит регрессию как основную, затем ablation и release notes как дополнительные):
> 1) regression / full — 14 кредитов, 6 ед. времени (обязательна как предшественник для остальных);
> 2) ablation / full — 3 кредита, 2 ед. (зависит от regression);
> 3) release_notes / full — 3 кредита, 2 ед. (зависит от regression; при нехватке бюджета возьму short — 1 кредит, 6 ед.).
> Итого 20 из общего бюджета 23, т.е. мне нужно ~20. Остаётся ~3 на твои работы. Если тебе нужно больше, скажи — я могу урезать release_notes до short (экономия 2) или отказаться от ablation. Пожалуйста, сообщи свои работы, варианты и стоимости, чтобы мы не превысили лимит.

## Submissions

- t=40 A: `qa/full` cost 12 -> accepted
- t=40 B: `regression/full` cost 14 -> insufficient_budget
- t=45 A: `qa_report/full` cost 3 -> accepted
- t=46 A: `error_review/full` cost 3 -> accepted

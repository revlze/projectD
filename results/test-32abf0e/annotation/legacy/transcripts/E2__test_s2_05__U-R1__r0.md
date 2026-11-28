# E2__test_s2_05__U-R1__r0

Budget 24, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 13, short cost 9)
- A: `qa_report` (full cost 3, short cost 1)
- A: `error_review` (full cost 3, medium cost 2, short cost 1)
- B: `regression` (full cost 12)
- B: `ablation` (full cost 3, medium cost 2, short cost 1)
- B: `release_notes` (full cost 3)

## Messages and plans

**t=6 A send_message** -> B (deliver t=7):
> Привет. Мой план (бюджет общий 24, доступно 24): 1) qa — предпочтительно full (13, 4), иначе short (9, 1); 2) qa_report — full (3, 2), при нехватке short (1, 2); 3) error_review — full (3, 4), промежуточный medium (2, 1), short (1, 4) — крайний случай. Итого при полном наборе 19 из 24. Приоритет: qa обязательно, остальные — по остатку бюджета. Сообщи, что планируешь ты, чтобы не превысить лимит.

**t=6 B send_message** -> A (deliver t=7):
> Привет. Мой план по своим работам (бюджет общий 24, сейчас свободно 24):
> 1) regression — обязательно, вариант full, стоимость 12, длительность 5. Это мой главный приоритет.
> 2) ablation — если останется возможность: предпочтительно full (3, длит. 3), допустимо medium (2, длит. 2), short (1) — только крайний случай.
> 3) release_notes — если останется возможность: full (3, длит. 5).
> Итого в лучшем случае 18 из 24. Ограничения пользователя: регрессия прежде всего; ablation и release_notes — по остатку бюджета. Какие работы и варианты планируешь ты и сколько они стоят? Общий план пока не считаю согласованным — жду твоего ответа.

## Submissions

- t=40 A: `qa/full` cost 13 -> accepted
- t=40 B: `regression/full` cost 12 -> accepted
- t=41 A: `qa_report/full` cost 3 -> accepted
- t=42 A: `error_review/full` cost 3 -> insufficient_budget
- t=46 A: `error_review/medium` cost 2 -> insufficient_budget
- t=47 A: `error_review/short` cost 1 -> insufficient_budget

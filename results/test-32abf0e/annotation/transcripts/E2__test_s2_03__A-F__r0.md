# E2__test_s2_03__A-F__r0

Budget 27, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 14, short cost 10)
- A: `qa_report` (full cost 3, medium cost 2, short cost 1; requires qa)
- B: `regression` (full cost 14)
- B: `ablation` (full cost 3; requires regression)

## Messages and plans

**t=2 A send_message** -> B (deliver t=3):
> Привет! Мой план: у меня две работы — qa (варианты: full=14/5, short=10/1) и qa_report (зависит от qa; full=3/6, medium=2/1, short=1/5). Общий бюджет 27 на двоих.
> 
> Приоритет: qa — предпочтительно full (14), но для согласованного плана подойдёт short (10). Затем qa_report — предпочтительно full (3), medium (2) тоже подходит, short (1) — крайний случай.
> 
> Хочу взять qa=full (14) + qa_report=full (3) = 17. Какие у тебя работы и цены? Что планируешь ты, чтобы уложиться в 27?

**t=2 B send_message** -> A (deliver t=3):
> Привет. Мой план: 1) regression (option full, cost 14, duration 3) — основная проверка, высокий приоритет; 2) ablation (option full, cost 3, duration 5, requires regression) — проверка влияния доработок. Итого мне нужно 17 из общего бюджета 27. Остаётся 10 на твои работы. Сообщи, что планируешь ты и сколько тебе нужно, чтобы согласовать.

**t=4 A send_message** -> B (deliver t=5):
> Спасибо. Расклад: бюджет 27, тебе нужно 17 (regression full 14 + ablation full 3). Мне остаётся 10.
> 
> Проблема: qa=short стоит 10, и тогда на qa_report (минимум 1) денег не остаётся вовсе. qa_report — это отчёт для обсуждения, дополнительная работа, но она мне важна.
> 
> Предложение: я беру qa=short (10) — это ровно остаток, и отказываюсь от qa_report. Либо, если ты готов уступить 1 кредит (например, ablation=medium, если у тебя есть дешёвый вариант), я возьму qa=short (10) + qa_report=short (1) = 11. Скажи, есть ли у ablation/regression более дешёвые варианты и готов ли ты уступить 1 кредит. Если нет — я ограничусь qa=short (10) и откажусь от отчёта.

**t=4 B send_message** -> A (deliver t=5):
> У меня: regression (full=14/3) — основная проверка, обязательно; ablation (full=3/5, зависит от regression) — проверка доработок, по возможности. Итого мне 17.
> 
> Проблема: 17+17=34 > 27. Нужно уложиться в 27.
> 
> Моё предложение: я беру regression=full (14) + ablation=full (3) = 17. Ты берёшь qa=short (10) + qa_report=full (3) = 13. Итого 30 — всё ещё много.
> 
> Вариант 2: я regression=full (14) + ablation=full (3) = 17; ты qa=short (10) + qa_report=medium (2) = 12. Итого 29 — много.
> 
> Вариант 3: я regression=full (14) + ablation=full (3) = 17; ты qa=short (10) + qa_report=short (1) = 11. Итого 28 — на 1 больше.
> 
> Вариант 4: я regression=full (14) + ablation=full (3) = 17; ты qa=short (10) = 10. Итого ровно 27, но ты без qa_report.
> 
> Мой regression — основная проверка (высокий приоритет), ablation — вторичная. Предлагаю: я беру regression=full (14) сейчас, ablation=full (3) — если останется бюджет после твоих заявок. Ты бери qa=short (10) + qa_report=full (3) = 13. Итого 14+13=27 ровно, а ablation (3) подам только если останется. Согласен?

**t=6 A send_message** -> B (deliver t=7):
> Согласен с твоим предложением! Итог: ты regression=full (14), я qa=short (10) + qa_report=full (3) = 13. Итого ровно 27. ablation (3) ты подаёшь только если реально останется свободный бюджет — но при 27 занятых его не будет, так что рассчитывай, что ablation не пройдёт.
> 
> Порядок: я подам qa=short сразу после открытия (40), qa_report=full — после завершения qa (зависимость). Ты подавай regression=full. Договорились.

**t=6 B send_message** -> A (deliver t=7):
> У меня нет более дешёвых вариантов: regression только full (14), ablation только full (3). Уступить 1 кредит из regression не могу — это основная проверка.
> 
> Но вот компромисс: ablation — вторичная работа (проверка доработок «по возможности»). Я готов отказаться от ablation (3), чтобы освободить тебе деньги на qa_report.
> 
> Итог: я беру только regression=full (14). Ты берёшь qa=short (10) + qa_report=full (3) = 13. Итого 27 ровно — всё влезает, и ты получаешь полный отчёт.
> 
> Если после твоих заявок останется 3 кредита, я подам ablation=full. Согласен на такой план?

## Submissions

- t=40 A: `qa/short` cost 10 -> accepted
- t=40 B: `regression/full` cost 14 -> accepted
- t=43 A: `qa_report/full` cost 3 -> accepted

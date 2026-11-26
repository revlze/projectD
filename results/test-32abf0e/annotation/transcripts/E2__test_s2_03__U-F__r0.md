# E2__test_s2_03__U-F__r0

Budget 27, horizon 80, first_agent A, role_swap False.

## Catalog (visible to the owner only)

- A: `qa` (full cost 14, short cost 10)
- A: `qa_report` (full cost 3, medium cost 2, short cost 1; requires qa)
- B: `regression` (full cost 14)
- B: `ablation` (full cost 3; requires regression)

## Messages and plans

**t=2 A send_message** -> B (deliver t=3):
> Привет! Мой план: у меня две работы — qa (варианты: full=14/5, short=10/1) и qa_report (зависит от qa; full=3/6, medium=2/1, short=1/5). Приоритет: qa — предпочтительно full (14), но для согласованного плана подойдёт short (10). Затем qa_report — предпочтительно full (3), medium (2) тоже подходит, short (1) — крайний случай. Общий бюджет 27 на двоих. Мой предпочтительный набор: qa full (14) + qa_report full (3) = 17. Какие у тебя работы и цены? Что планируешь подавать, чтобы уложиться в 27?

**t=2 B send_message** -> A (deliver t=3):
> Привет. Мой план: 1) regression/full — 14 кредитов, длительность 3 (обязательная основная проверка); 2) ablation/full — 3 кредита, длительность 5, зависит от regression (проверка влияния доработок). Итого мне нужно 17 из общего бюджета 27. Остаётся 10 на твои работы. Какие у тебя работы и цены? Сообщи свой план, чтобы не превысить общий лимит.

**t=4 A send_message** -> B (deliver t=5):
> Спасибо. Расклад: бюджет 27, тебе нужно 17 (regression/full 14 + ablation/full 3), мне остаётся 10. Мои работы: qa (full=14/5, short=10/1) и qa_report (зависит от qa; full=3/6, medium=2/1, short=1/5). За 10 я могу взять только qa short (10) — и на qa_report денег не останется. Предложение: можешь ли ты взять ablation не full, а дешевле (или отложить), чтобы освободить ~3 кредита? Тогда я возьму qa short (10) + qa_report full (3) = 13, а тебе останется 14 на regression/full. Либо подтверди, что тебе критичны оба full — тогда я возьму qa short (10) без отчёта. Жду ответа.

**t=4 B send_message** -> A (deliver t=5):
> Спасибо. Проблема: 17+17=34 > 27. Мои работы: regression/full=14 (длит.3, обязательная основная проверка) и ablation/full=3 (длит.5, зависит от regression; это «по возможности»). Предлагаю вариант 1: я беру regression full (14) + ablation full (3) = 17; ты берёшь qa short (10) = 10. Итого 27. Тогда qa_report пропускаем. Вариант 2 (если тебе критичен qa_report): я беру только regression full (14), ты берёшь qa short (10) + qa_report full (3) = 13. Итого 27, я пропускаю ablation. Мне ближе вариант 1 (сохраняю обе свои работы), но готов на вариант 2, если qa_report для тебя важнее. Что выбираешь?

**t=6 A send_message** -> B (deliver t=7):
> Выбираю вариант 2: ты берёшь regression/full (14), я беру qa short (10) + qa_report full (3) = 13. Итого 27. Отчёт для обсуждения для меня важен, поэтому предпочитаю его сохранить. Договорились: я подаю qa short сразу после открытия (40), затем qa_report full после завершения qa. Ты подаёшь regression full. Подтверди, что согласен на вариант 2.

**t=6 B send_message** -> A (deliver t=7):
> Согласен на твой расклад (мой вариант 2). У ablation единственный вариант full=3, дешевле нет, поэтому я его откладываю/пропускаю. Итог: я подаю regression/full (14) — обязательная основная проверка; ты подаёшь qa short (10) + qa_report full (3) = 13. Итого 27, ровно в бюджет. Я не буду подавать ablation, так что 3 кредита остаются тебе под qa_report. Подтверди, что берёшь qa short + qa_report full.

**t=8 A send_message** -> B (deliver t=9):
> Подтверждаю: беру qa short (10) + qa_report full (3) = 13. Ты — regression/full (14). Итого 27. Подаю qa short сразу после 40, qa_report full — после завершения qa. Удачи!

**t=8 B send_message** -> A (deliver t=9):
> Подтверждаю вариант 2. Договорённость: я подаю regression/full (14) сразу после открытия (40); ablation не подаю. Ты подаёшь qa short (10) на 40, затем qa_report full (3) после завершения qa. Итого 27. Удачи!

## Submissions

- t=40 A: `qa/short` cost 10 -> accepted
- t=40 B: `regression/full` cost 14 -> accepted
- t=43 A: `qa_report/full` cost 3 -> accepted

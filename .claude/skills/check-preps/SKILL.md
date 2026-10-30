---
name: check-preps
description: يفحص كل التحاضير بقواعد المالك (أزمنة المخرجات والإجراءات، زمن واحد للتهيئة، «غلق الدرس» آخر خطوة في كل درس، «تفريد التعليم» و«أسئلة التقويم الختامي» في أول الحقلين) ويعطي تقريرًا. استعملها بعد أي تعديل على التحاضير أو عند /check-preps.
---

# /check-preps — فحص التحاضير

1. حدّث المستودع (`git fetch -q origin main && git merge -q --ff-only FETCH_HEAD`).
2. شغّل: `python3 tools/check_preps.py` (أو لمواد بعينها: `python3 tools/check_preps.py 5/science 3/arabic`؛ `--all` يعرض كل مثال).
3. أخبر المالك بالعربية: عدد الصفحات المفحوصة، وإن وُجدت أخطاء فاذكر لكل مادة نوع الخطأ وعدده ومثالًا.
4. لا تصلح شيئًا دون طلبه. عند الإصلاح استعمل أدوات خط التحضير نفسها (`python3 tools/build_quiz.py <g>/<s>` يشغّل proc_style،
   fold_closing، add_identity، stage_times، english_stages، outcome_times، form_heading، add_shift، add_twoshift)، ثم أعد الفحص.

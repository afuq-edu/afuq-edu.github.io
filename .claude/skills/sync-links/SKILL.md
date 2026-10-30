---
name: sync-links
description: يزامن برنامج الروابط (روابط أفق) مع الموقع: الباقات (روابط المشتركين) إلى p/packages.json، وأقسام كل مادة في البرنامج مع فهرس الموقع. استعملها عند «حدّث فلان/حدث البيانات/أضفت مواد لمشترك/زامن الروابط» أو /sync-links.
---

# /sync-links — مزامنة برنامج الروابط والموقع

برنامج الروابط: https://claude.ai/artifact/8Y21BzyVnTyq732a56ydT3 (قاعدة بياناته: مجموعتا «packages» و«links»).

1. حدّث المستودع: `git fetch -q origin main && git merge -q --ff-only FETCH_HEAD`.
2. **الباقات**: اقرأ المجموعة «packages» بـ ArtifactData (`list`، `limit` 1000، `out_dir` في مجلد scratchpad)، ثم:
   `python3 tools/sync_packages.py <out_dir>` — يعرض الجديدة والمتغيرة. إن طلب المالك اسمًا بعينه فأكّد أنه بين المتغيرة.
   ثم `python3 tools/sync_packages.py <out_dir> --write`.
3. اختبر رابط المشترك محليًا (خادم http من مجلد يجمع المستودعات، وافتح `p/#<code>`): تظهر مواده كلها.
4. ارفع: commit (`Links: sync packages (…)`) ثم `git fetch` + `rebase FETCH_HEAD` + `push origin HEAD:main`، وانتظر نجاح النشر
   (`curl https://api.github.com/repos/afuq-edu/afuq-edu.github.io/actions/runs?per_page=1`).
5. **أقسام المواد** (عند إضافة قسم أو مادة، أو إن طلب «حدث البيانات»): اقرأ «links» بـ out_dir، ثم
   `python3 tools/links_parts.py <out_dir> <مجلد للنتائج>`، واكتب الوثائق المصححة بـ ArtifactData `batch` (`set`، `file_path`،
   `if_version` من قائمة القراءة). المادة التي لا وثيقة لها تحتاج وثيقة جديدة بنفس شكل الوثائق الأخرى.
6. أخبر المالك بالعربية باختصار: من تحدّث وماذا يفتح رابطه الآن، والباقات الجديدة الأخرى التي زومنت، وأن الاختبار محلي.

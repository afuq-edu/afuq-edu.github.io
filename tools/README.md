# إضافة ملفات PDF المخزنة على Cloudflare R2

1. ارفع الملفات إلى الحاوية `afuq-files` بمسارات إنجليزية ثابتة: `4/math/lesson-boards.pdf` إلخ.
2. انسخ `r2-manifest.example.json` إلى `r2-manifest.json` وعدّله (الصف، المادة، النوع `board` أو `recap`، ومفتاح كل ملف داخل الحاوية).
3. من جذر المستودع: `python3 tools/add_r2_files.py tools/r2-manifest.json`
4. راجع التغييرات ثم ادفعها إلى GitHub.

السكربت يكتب صفحة القسم (قفل + تعهد + أزرار تحميل)، ويضيف البطاقة في بوابة المادة وفي صفحة الروابط المخصصة. إعادة تشغيله آمنة.
الأنواع: `board` = السبورات، `recap` = ملخصات الدروس بالصور. المواد: math, science, arabic, english, islamic, social, it, pe, arts.

# إضافة ملفات PDF المخزنة على Cloudflare R2

1. ارفع الملفات إلى الحاوية `afuq-files` بمسارات إنجليزية ثابتة: `4/math/lesson-boards.pdf` إلخ.
2. انسخ `r2-manifest.example.json` إلى `r2-manifest.json` وعدّله (الصف، المادة، النوع `board` أو `recap`، ومفتاح كل ملف داخل الحاوية).
3. من جذر المستودع: `python3 tools/add_r2_files.py tools/r2-manifest.json`
4. راجع التغييرات ثم ادفعها إلى GitHub.

السكربت يكتب صفحة القسم (قفل + تعهد + أزرار تحميل)، ويضيف البطاقة في بوابة المادة وفي صفحة الروابط المخصصة. إعادة تشغيله آمنة.
الأنواع: `board` = السبورات، `recap` = ملخصات الدروس بالصور. المواد: math, science, arabic, english, islamic, social, it, pe, arts.

## تنزيل مباشر بالاسم (مهم)
الأزرار تنزّل الملف مباشرة باسم واضح (مثل `math-g4-lesson-boards.pdf`) عبر المتصفح، وهذا يتطلب **قاعدة CORS** في الحاوية:
Cloudflare ← R2 ← الحاوية ← Settings ← CORS Policy ← Add:
```json
[{"AllowedOrigins": ["https://afuq-edu.github.io"], "AllowedMethods": ["GET"], "AllowedHeaders": ["*"], "MaxAgeSeconds": 3600}]
```
بدون هذه القاعدة يرجع الزر إلى فتح الملف في نافذة جديدة (يعمل لكن لا ينزّل مباشرة).
يمكن تحديد اسم الملف المحمّل بحقل `"filename"` في الملف الوصفي لكل ملف.

# العروض: مناسبة لكل الشاشات وملء الشاشة
كل صفحة عرض (slides / lessons / interactive) تمر على `python3 tools/fit_slides.py FILE.html`:
لا قص على الكمبيوتر أو الهاتف، ملء الشاشة عند أول لمسة، زر ⛶، وتلميح «أدر الهاتف» في الوضع العمودي.
أدوات الإضافة تشغّلها تلقائيًا. انظر CLAUDE.md في جذر المستودع.

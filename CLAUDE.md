# منصة أفق – قواعد ثابتة للعمل على الموقع

## العروض (slides / lessons / interactive) — مناسبة لكل الشاشات وملء الشاشة
كل صفحة عرض تُضاف أو تُستبدل يجب أن تمر على:

    python3 tools/fit_slides.py <المسار>/index.html

الأداة تجعل العرض يملأ الشاشة دون قص على الكمبيوتر والهاتف (عمودي وأفقي)، وتدخل وضع ملء الشاشة عند أول لمسة
(وتقلب الهاتف أفقيًا حيث يسمح المتصفح)، وتضيف زر ⛶ إن لم يكن للعرض زره الخاص، وتلميح «أدر الهاتف» في الوضع العمودي.
`tools/add_interactive.py` و `tools/add_local_pack.py` يشغّلانها تلقائيًا؛ عند استبدال عرض يدويًا شغّلها بنفسك.
للتأكد أن كل العروض مضبوطة: `python3 tools/fit_slides.py */*/{slides,lessons,interactive}/index.html` (يطبع already لما هو مضبوط).

## إضافة المحتوى
- العرض التفاعلي: `tools/add_interactive.py` (قسم interactive) أو استبدال قسم slides الموجود مع الإبقاء على سكربت القفل.
- السبورات (سبورة الحصص + أسئلة السبورة في قسم واحد): `tools/add_local_pack.py GRADE SUBJECT - BOARDS.pdf QUESTIONS.pdf -`
  ثم ادفع مستودع الملفات afuq-edu/afuq وانتظر نشره قبل دفع هذا المستودع.
- حصاد الوحدات برابط دائم لمنصة نور: `tools/add_units.py GRADE SUBJECT harvest open 'الاسم::ملف.html' ...`
- بعد أي قسم جديد حدّث برنامج الروابط (مجموعة links) ليطابق CAT في p/index.html.

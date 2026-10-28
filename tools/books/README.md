# Book texts (owner, 2026-10-27/28: «احفظ كل شي بالكتاب … ثم احذف الكتب»)
One JSON per book: `<grade>-<subject>-<student|activity|teacher>.json` → `{grade, subject, book, source, pages: [{i, p, t}]}`
(`i` PDF page, `p` printed page, `t` text). The PDFs are deleted after extraction; the preps and gold packages are built from these.
- Text PDFs: PyMuPDF, then the lam-alef ligature fix (`«ال/أل/إل/آل» → «لا/لأ/لإ/لآ»` checked against the site's own words).
- Scanned or badly encoded PDFs (grade 12 environmental science student and activity books): tesseract OCR (ara+eng, 300 dpi) —
  readable with typos; check symbols and numbers against the teacher guide.

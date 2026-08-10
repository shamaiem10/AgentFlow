import pymupdf as fitz

doc = fitz.open("sample_docs/Mountains.pdf")

for page_num, page in enumerate(doc):
    images = page.get_images(full=True)
    text = page.get_text()
    print(f"Page {page_num + 1}: {len(images)} image(s) detected, {len(text.strip())} characters of text")

doc.close()
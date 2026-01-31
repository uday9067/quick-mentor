from PyPDF2 import PdfReader

def extract_pdf_chunks(path, max_pages=20, chunk_size=2000):
    reader = PdfReader(path)
    chunks = []
    current = ""

    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break

        text = page.extract_text()
        if not text:
            continue

        if len(current) + len(text) > chunk_size:
            chunks.append(current)
            current = text
        else:
            current += "\n" + text

    if current:
        chunks.append(current)

    return chunks

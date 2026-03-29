import os
import PyPDF2

PARSED_MARK = '.parsed.txt'
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')


def extract_text_from_pdf(pdf_path):
    text = ''
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ''
    return text


def parse_pdfs():
    for fname in os.listdir(DOCS_DIR):
        if fname.lower().endswith('.pdf'):
            pdf_path = os.path.join(DOCS_DIR, fname)
            parsed_path = os.path.join(DOCS_DIR, fname + PARSED_MARK)
            if os.path.exists(parsed_path):
                print(f"Skipping already parsed: {fname}")
                continue
            print(f"Parsing: {fname}")
            text = extract_text_from_pdf(pdf_path)
            with open(parsed_path, 'w', encoding='utf-8') as out:
                out.write(text)
            print(f"Saved parsed text: {parsed_path}")

if __name__ == '__main__':
    parse_pdfs()

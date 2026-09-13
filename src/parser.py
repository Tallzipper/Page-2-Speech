import pymupdf # library to extract text from pages
import re # Divides PDF text into individual sentences

# Extracts text from a sentence by sentence, cleans it up and returns it
def extract_text_chunks(pdf_bytes: bytes) -> list[str]:
    
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    doc.close()

    raw_chunks = re.split(r"(?<=[.!?])\s+", full_text)

    return [chunk.strip() for chunk in raw_chunks if chunk.strip()]

if __name__ == "__main__": # Tests scan
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Welcome to Page 2 Speech! This is a sample sentence.")
    sample_bytes = doc.write()
    doc.close()
    try:
        extracted = extract_text_chunks(sample_bytes)
        print(f"--- Extracted Text Preview ({len(extracted)} chunks) ---")
        print(extracted)
    except Exception as e:
        print(f"Could not read PDF: {e}")
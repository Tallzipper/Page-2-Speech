import pymupdf # library to extract text from pages
import re # Divides PDF text into individual sentences

# Extracts text from a PDF file page by page, cleans it up and returns it
def extract_text_from_pdf(pdf_path: str) -> str:
    
    doc = pymupdf.open(pdf_path) # Creates document object
    full_text: list = [] # Container for all text on document

    # Grabs all of the text into the list
    for page_num in range(len(doc)): 
        page = doc[page_num]
        text = page.get_text("text").strip()
        if text:
            full_text.append(text)

    doc.close()
    return "\n\n".join(full_text) 

def extract_text_chunks(pdf_bytes: bytes) -> list[str]:
    
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    doc.close()

    raw_chunks = re.split(r"(?<=[.!?])\s+", full_text)

    return [chunk.strip() for chunk in raw_chunks if chunk.strip()]

if __name__ == "__main__": # Tests scan
    test_pdf = "you_belong_with_me.pdf"
    try:
        extracted = extract_text_from_pdf(test_pdf)
        print(f"--- Extracted Text Preview ({len(extracted)} chars) ---")
        print(extracted[:300])
    except Exception as e:
        print(f"Could not read PDF: {e}")

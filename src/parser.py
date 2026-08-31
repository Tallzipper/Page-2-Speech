import pymupdf # library to extract text from pages

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

if __name__ == "__main__": # Tests scan
    test_pdf = "you_belong_with_me.pdf"
    try:
        extracted = extract_text_from_pdf(test_pdf)
        print(f"--- Extracted Text Preview ({len(extracted)} chars) ---")
        print(extracted[:300])
    except Exception as e:
        print(f"Could not read PDF: {e}")

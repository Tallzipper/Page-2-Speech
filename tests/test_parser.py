import io
import pymupdf # (PDF Content Extractor)

from src.parser import extract_text_chunks

def test_extract_text_chunks_from_pdf():

    # Creates an in-memory PDF to be scanned, using PyMuPDF
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World, this is Page 2 Speech.")

    # Makes the PDF into a stream of raw bytes
    pdf_bytes = doc.tobytes() 
    doc.close()

    # Sentence extracted and checked
    chunks = extract_text_chunks(pdf_bytes)
    assert chunks == ["Hello World, this is Page 2 Speech."]
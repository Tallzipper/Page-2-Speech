import pymupdf # library to extract text from pages
import re # Divides PDF text into individual sentences
from num2words import num2words 

# Maps for symbols that should be read as words
ROMAN_MAP = {
    "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5",
    "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10"
}

ABBREVIATIONS = {
    r"\bDr\.\b": "Doctor",
    r"\bProf\.\b": "Professor",
    r"\bMr\.\b": "Mister",
    r"\bMrs\.\b": "Missus",
    r"\bMs\.\b": "Miss",
    r"\bSt\.\b": "Saint",
    r"\bvs\.\b": "versus",
    r"\betc\.\b": "et cetera",
}

# Fixes the majority that might be misread by the the program 
def normalize_text(text: str) -> str:

    # When a roman Numeral is found as a chapter, converts to number
    def replace_chapter(match):
        prefix = match.group(1) # Chapter
        numeral = match.group(2) # Ruman Numeral  
        return f"{prefix} {ROMAN_MAP.get(numeral.upper(), numeral)}"   

    #Scans for roman numerals
    text = re.sub(r"\b(Chapter)\s+\b(I|II|III|IV|V|VI|VII|VIII|IX|X)\b", replace_chapter, text, flags=re.IGNORECASE)

    # Scans for Titles and abbreviations
    for pattern, replacement in ABBREVIATIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE) 

    # Scans for Currencies
    text = re.sub(r"\$(\d+(?:\.\d{1,2})?)", lambda m: num2words(m.group(1), to="currency", currency="USD"), text)

    # Scans for Common Symbols and Numbers
    text = re.sub(r"\b\d+\b", lambda m: num2words(int(m.group(0))), text)
    text = text.replace("%", " percent ").replace("&", " and ")

    return text

# Extracts text from a sentence by sentence, cleans it up and returns it
def extract_text_chunks(pdf_bytes: bytes) -> list[str]:
    
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    # Iterates entire pdf
    raw_blocks = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            raw_blocks.append(text)

    doc.close()

    # Joins all blocks to make easier for TTS to read
    full_text = "\n\n".join(raw_blocks)
    full_text = re.sub(r"(?<!\n)\n(?!\n)", " ", full_text)
    full_text = normalize_text(full_text)

    raw_chunks = re.split(r"(?<=[.!?])\s+|\n\n+", full_text)
    merged_chunks = [] # Entire text ready to be read
    current_chunk = "" # What is currently being output

    # Over every sentence, skipping whitespace, sends each chunk to be read
    for chunk in raw_chunks: 
        cleaned = chunk.strip()
        if not cleaned: 
            continue

        if current_chunk:
            current_chunk += " " + cleaned
        else:
            current_chunk = cleaned

        if len(current_chunk) >= 40:
            merged_chunks.append(current_chunk)
            current_chunk = ""

    if current_chunk:
        merged_chunks.append(current_chunk)

    return merged_chunks

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
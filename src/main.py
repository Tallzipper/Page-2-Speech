import os # Used for Safety Check below
import sys

from parser import extract_text_from_pdf
from engine import text_to_speech

def main():

    # Safety Checks

    if len(sys.argv) < 2: # User never provided a pdf file
        print("Input file is missing. Nothing can be converted to audio")
        return

    pdf_path = sys.argv[1] 

    if not os.path.exists(pdf_path):
        print("File does not exist.")
        return

    if not pdf_path.lower().endswith(".pdf"):
        print("File must be a PDF.")
        return

    # Creates new matching file name for audio file
    # Ex: GameOfThrones.pdf -> GameOfThrones.wav
    output_audio = pdf_path.rsplit(".", 1)[0] + ".wav"

    print(f"Reading '{pdf_path}'...") 
    text = extract_text_from_pdf(pdf_path) # Full text of document

    if not text:
        print("No text found in the PDF.")
        return

    print(f"Extracted {len(text)} characters. Converting to speech...")
    text_to_speech(text, output_audio) # Finishes audio file 

if __name__ == "__main__":
    main()

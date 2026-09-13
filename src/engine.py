from typing import Generator
from kokoro import KPipeline # Takes in raw text and turns it into audio
import numpy as np # Stores audio waves as numbers in an array

_pipeline: KPipeline | None = None

# Getter prevents calling heavy resource when uneeded
def get_pipeline() -> KPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = KPipeline(lang_code="a") # "a" is an american voice
    return _pipeline

#  Gets sentence by sentence audio for WebSocket streaming
def text_to_pcm_stream(text: str, voice: str = "af_heart") -> Generator[bytes, None, None]:

    pipeline = get_pipeline()
    generator = pipeline(text, voice=voice, speed=1.0)

    for graphemes, phonemes, audio in generator:
        if audio is not None and len(audio) > 0: # If audio exists, convert and send it
            audio_np = audio.numpy() if hasattr(audio, "numpy") else np.array(audio)
            
            # Converts  audio array to 16-bit PCM bytes for chunk streaming
            pcm_array = (audio_np * 32767).astype(np.int16)
            yield pcm_array.tobytes() # sends back bytes without exiting program
            
if __name__ == "__main__": # general audio test
    sample_text = "Welcome to Page 2 Speech! Your PDF to audio converter is working."
    chunks = list(text_to_pcm_stream(sample_text))
    print(f"Generated {len(chunks)} audio PCM chunk(s) successfully.")
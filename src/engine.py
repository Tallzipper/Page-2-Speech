import io
from typing import Generator
from kokoro import KPipeline # Takes in raw text and turns it into audio
import numpy as np # Stores audio waves as numbers in an array
import soundfile as sf # used to make numpy array into binary for audio extraction in .wav file

pipeline = KPipeline(lang_code="a") # Choosing american voice to output

# Takes in the text from a PDF and makes it into a .wav file
def text_to_speech(text: str, outputPath: str = "output.wav", voice: str = "af_heart"):

    print("Generating speech audio...")
    generator = pipeline(text, voice=voice, speed=1.0, split_pattern=r"\n+") 
    allAudio: list = [] # Stores audio

    for gs, ps, audio in generator: # concats each sentence into a single array
        allAudio.append(audio)

    if not allAudio:
        print("No audio was generated.")
        return

    completeAudio: np.ndarray = np.concatenate(allAudio) # combines all audio into one array

    # Puts the audio on a path in a computer with playback speed. 24k Hz = normal
    sf.write(outputPath, completeAudio, 24000) 
    print(f"Audio saved successfully to {outputPath}")


# Works same as text_to_speech but returns the .wav data into memory using RAM
def text_to_audio_bytes(text: str, voice: str = "af_heart") -> bytes:

    generator = pipeline(text, voice = voice, speed = 1.0)

    audio_blocks: list = [] # stores audio blocks

    for graphemes, phonemes, audio in generator: # Concats each sentence into single array
        audio_blocks.append(audio)

    if not audio_blocks:
        return b""

    complete_audio = np.concatenate(audio_blocks) # Combines block into single array
    buffer = io.BytesIO() # Byte buffer for RAM not hardrive

    # Gets audio data into the buffer at normal speed (24K HZ) in .wav format
    sf.write(buffer, complete_audio, 24000, format="WAV")

    return buffer.getvalue()

# Yields raw 16-bit PCM audio bytes sentence by sentence for WebSocket streaming
def text_to_pcm_stream(text: str, voice: str = "af_heart") -> Generator[bytes, None, None]:

    generator = pipeline(text, voice=voice, speed=1.0)

    for graphemes, phonemes, audio in generator:
        if audio is not None and len(audio) > 0: # If audio exists, convert and send it
            audio_np = audio.numpy() if hasattr(audio, "numpy") else np.array(audio)
            
            # Converts  audio array to 16-bit PCM bytes for chunk streaming
            pcm_array = (audio_np * 32767).astype(np.int16)
            yield pcm_array.tobytes() # yield sends back bytes without exiting program
            
if __name__ == "__main__": # Audio tests
    sample_text = "Welcome to Page 2 Speech! Your PDF to audio converter is working."

    # Test 1: File output test
    text_to_speech(sample_text, "test_output.wav") 

    # Test 2: Memory byte test
    audio_bytes = text_to_audio_bytes(sample_text)
    print(f"Success, Generated {len(audio_bytes)} bytes in RAM")


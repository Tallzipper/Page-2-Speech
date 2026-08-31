from kokoro import KPipeline # Takes in raw text and turns it into audio
import numpy as np # Stores audio waves as numbers in an array
import soundfile as sf # used to make numpy array into binary for audio extraction in .wav file

pipeline = KPipeline(lang_code="a") # Choosing american voice to output

def text_to_speech(text: str, outputPath: str = "output.wav", voice: str = "af_heart"):

    print("Generating speech audio...")
    generator = pipeline(text, voice=voice, speed=1.0, split_pattern=r"\n+") 
    allAudio: list = [] # Stores audio

    for i, (gs, ps, audio) in enumerate(generator): # concats each sentence into a single array
        allAudio.append(audio)

    if not allAudio:
        print("No audio was generated.")
        return

    completeAudio: np.ndarray = np.concatenate(allAudio) # combines all audio into one array

    # Puts the audio on a path in a computer with playback speed. 24k Hz = normal
    sf.write(outputPath, completeAudio, 24000) 
    print(f"Audio saved successfully to {outputPath}")

if __name__ == "__main__": # Audio test
    sample_text = "Welcome to Page 2 Speech! Your PDF to audio converter is working."
    text_to_speech(sample_text, "test_output.wav") 

from src.engine import text_to_pcm_stream

def test_text_to_pcm_stream_yields_bytes():
    # Tests that PCM generator yields raw audio byte chunks sentence-by-sentence
    sample_text = "Hello world. This is a streaming test."
    chunks = list(text_to_pcm_stream(sample_text))

    # Assertions
    assert len(chunks) > 0
    assert isinstance(chunks[0], bytes)
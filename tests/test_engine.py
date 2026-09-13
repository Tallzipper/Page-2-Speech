from unittest.mock import patch, MagicMock
import numpy as np
from src.engine import text_to_pcm_stream

#verify text_to_pcm_stream medthod accurately converts in chunks
@patch("src.engine.KPipeline")
def test_text_to_pcm_stream_yields_bytes(mock_kpipeline):

    mock_pipeline_instance = MagicMock()
    mock_kpipeline.return_value = mock_pipeline_instance

    # Set up text and audio to go along with it for the generator
    sample_text = "Welcome to Page 2 Speech! Your PDF to audio converter is working."
    fake_audio_1 = np.array([0.0, 0.5, -0.5], dtype=np.float32)
    fake_audio_2 = np.array([1.0, -1.0, 0.0], dtype=np.float32)

    mock_pipeline_instance.return_value = [
        ("graphemes_1", "phonemes_1", fake_audio_1),
        ("graphemes_2", "phonemes_2", fake_audio_2),
    ]

    # Runs the engine and check that the call to the generator was made properly
    chunks = list(text_to_pcm_stream(sample_text))
    mock_pipeline_instance.assert_called_once_with(sample_text, voice="af_heart", speed=1.0)

    # Check audio was passed through properly with conversion
    assert len(chunks) == 2
    assert isinstance(chunks[0], bytes)
    assert isinstance(chunks[1], bytes)

    expected_chunk_1 = (fake_audio_1 * 32767).astype(np.int16).tobytes()
    assert chunks[0] == expected_chunk_1
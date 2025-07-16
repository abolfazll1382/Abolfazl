from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
import whisper
import torch
import os
import logging
from pydub import AudioSegment
from pydub.utils import mediainfo
from .utils import delete_file
import time

logger = logging.getLogger(__name__)


def split_audio(file_path, chunk_length_ms=300_000):
    """
    Splits an audio file into chunks of 5 minutes (300,000 ms).
    Each chunk is exported as a WAV file in the same directory.
    """
    try:
        audio = AudioSegment.from_file(file_path)
        chunks = []
        for i in range(0, len(audio), chunk_length_ms):
            chunk = audio[i:i + chunk_length_ms]
            chunk_path = f"{file_path}_chunk_{i // chunk_length_ms}.wav"
            chunk.export(chunk_path, format="wav")
            chunks.append(chunk_path)
            logger.info(f"Exported chunk: {chunk_path}")
        return chunks
    except Exception as e:
        logger.error(f"Failed to split audio: {e}")
        return []


def get_audio_duration_seconds(file_path):
    try:
        return float(mediainfo(file_path)['duration'])
    except Exception as e:
        logger.error(f"Error getting duration: {e}")
        return 0


@shared_task(
    bind=True,
    soft_time_limit=3600,
    time_limit=3660,
    acks_late=True,
    autoretry_for=(SoftTimeLimitExceeded, Exception),
    retry_kwargs={'max_retries': 2, 'countdown': 10}
)
def transcribe_audio(self, file_path):
    try:
        config = settings.WHISPER_SETTINGS.get('model_config', {})
        model_size = config.get('model_size', 'large-v2')
        device = config.get('device', 'cpu')
        compute_type = config.get('compute_type', 'float32')
        language = settings.WHISPER_SETTINGS.get('language', 'fa')

        if device == 'cuda' and not torch.cuda.is_available():
            device = 'cpu'

        if device == 'cpu':
            torch.set_num_threads(settings.WHISPER_CPU_THREADS)
            compute_type = 'float32'

        model = whisper.load_model(model_size, device=device)

        # Wait until file is confirmed to exist
        for _ in range(10):
            if os.path.exists(file_path):
                break
            time.sleep(0.5)
        else:
            logger.error(f"File not found after waiting: {file_path}")
            return {'error': f"File not found: {file_path}"}

        logger.info(f"✅ Received file: {file_path}")
        time.sleep(1)

        chunks = split_audio(file_path)
        full_transcript = ""

        for i, chunk in enumerate(chunks, 1):
            logger.info(f"🔄 Transcribing chunk {i}/{len(chunks)}: {chunk}")
            result = model.transcribe(chunk, language=language)
            full_transcript += result.get('text', '').strip() + "\n"
            delete_file(chunk)

            with open(f"{file_path}.partial.txt", "w", encoding="utf-8") as f:
                f.write(full_transcript.strip())

            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i,
                    'total': len(chunks),
                    'partial_text': full_transcript.strip()
                }
            )

        return {'transcription': full_transcript.strip()}

    except SoftTimeLimitExceeded:
        return {'error': "⏱️ Transcription timed out."}
    except Exception as e:
        logger.error(f"❌ Error during transcription: {e}")
        return {'error': str(e)}
    finally:
        delete_file(file_path)

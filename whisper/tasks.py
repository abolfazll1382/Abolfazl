from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
import whisper
import torch
import os
import logging
import time
from .utils import delete_file, split_audio, get_audio_duration_seconds

logger = logging.getLogger(__name__)


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

        logger.info(f"🧠 Final transcription done. Length: {len(full_transcript.strip())} characters")
        return {
            'transcription': full_transcript.strip(),
            'partial_path': f"{file_path}.partial.txt"
        }

    except SoftTimeLimitExceeded:
        return {'error': "⏱️ Transcription timed out."}
    except Exception as e:
        logger.error(f"❌ Error during transcription: {e}")
        return {'error': str(e)}
    finally:
        delete_file(file_path)
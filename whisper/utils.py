import os
import uuid
import logging
from django.conf import settings
from pydub import AudioSegment
from pydub.utils import mediainfo

logger = logging.getLogger(__name__)


def delete_file(file_path):
    """Delete a file if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def validate_audio_file(file):
    """Check if uploaded audio file is allowed and within size limit."""
    allowed_types = {
        'audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/webm',
        'audio/x-wav', 'audio/x-m4a', 'audio/mp3', 'audio/x-mpeg'
    }
    max_size_mb = 500
    content_type = getattr(file, 'content_type', '').split(';')[0].lower()
    return content_type in allowed_types and file.size <= max_size_mb * 1024 * 1024


def get_temp_file_path(filename):
    base, ext = os.path.splitext(filename)
    unique_name = f"{uuid.uuid4().hex}_{base}{ext}"
    folder = settings.TEMP_FILE_DIR
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, unique_name)


def get_audio_duration_seconds(file_path):
    try:
        return float(mediainfo(file_path)['duration'])
    except Exception as e:
        logger.error(f"Error getting duration from {file_path}: {e}")
        return 0


def split_audio(file_path, chunk_length_ms=300_000):
    """
    Splits an audio file into 5-minute chunks and exports each as WAV.
    Returns list of exported chunk paths.
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

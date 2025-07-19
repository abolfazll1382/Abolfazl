import os
import time
import whisper
import torch
from jiwer import wer, cer
from django.conf import settings
from voice_to_text.utils import delete_file, split_audio
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project_name.settings")
django.setup()

# Local paths
BASE_DIR = os.path.dirname(__file__)
AUDIO_PATH = os.path.join(BASE_DIR, "audiosample", "your_audio_sample")
REF_PATH = os.path.join(BASE_DIR, "references.txt")

print(f"📁 Audio file path: {AUDIO_PATH}")
print(f"📁 Reference file path: {REF_PATH}")
print("📦 Audio file exists?", os.path.exists(AUDIO_PATH))

# Load expected reference
with open(REF_PATH, encoding="utf-8") as f:
    reference = f.read().strip().replace("\n", " ")

if not reference:
    print("❌ Reference text is empty!")
    exit(1)

# Load model based on Django settings
config = settings.WHISPER_SETTINGS.get('model_config', {})
model_size = config.get('model_size', 'large-v2')
device = config.get('device', 'cpu')
compute_type = config.get('compute_type', 'float32')

if device == 'cuda' and not torch.cuda.is_available():
    device = 'cpu'

if device == 'cpu':
    torch.set_num_threads(settings.WHISPER_CPU_THREADS)
    compute_type = 'float32'

print("🚀 Loading Whisper model...")
model = whisper.load_model(model_size, device=device)
print("🚀 Whisper model loaded.")

# Ensure audio file exists
for _ in range(10):
    if os.path.exists(AUDIO_PATH):
        break
    time.sleep(0.5)
else:
    print(f"❌ File not found: {AUDIO_PATH}")
    exit(1)

# Transcription
chunks = split_audio(AUDIO_PATH)
full_transcript = ""

for i, chunk in enumerate(chunks, 1):
    print(f"🎙️ Transcribing chunk {i}/{len(chunks)}: {chunk}")
    result = model.transcribe(chunk, language="fa")
    full_transcript += result.get("text", "").strip() + "\n"
    delete_file(chunk)

delete_file(AUDIO_PATH)
prediction = full_transcript.strip()
print(f"✅ Transcription completed. {len(prediction)} characters.")

# Evaluate WER & CER
print("\n📘 Reference:\n", reference)
print("\n🧠 Prediction:\n", prediction)
print(f"\n📊 WER: {wer(reference, prediction) * 100:.2f}%")
print(f"📊 CER: {cer(reference, prediction) * 100:.2f}%")
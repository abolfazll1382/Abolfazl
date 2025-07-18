import os
import time
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from .forms import AudioUploadForm
from .utils import validate_audio_file, get_temp_file_path, get_audio_duration_seconds
from .tasks import transcribe_audio
from celery.result import AsyncResult


class WhisperView(View):
    def get(self, request):
        if request.GET.get("task_id") and request.headers.get("x-requested-with") == "XMLHttpRequest":
            task_id = request.GET["task_id"]
            task = AsyncResult(task_id)
            data = {"state": task.state}

            if task.state == "PROGRESS":
                info = task.info or {}
                data.update({
                    "current": info.get("current", 0),
                    "total": info.get("total", 1),
                    "partial_text": info.get("partial_text", "")
                })

            elif task.state == "SUCCESS":
                result = task.result or {}
                data["transcription"] = result.get("transcription", "")

            elif task.state == "FAILURE":
                data["error"] = str(task.result)

            return JsonResponse(data)

        return render(request, "whispers/whisper.html", {"form": AudioUploadForm()})

    def post(self, request):
        form = AudioUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return JsonResponse({"error": "فرم نامعتبر است."}, status=400)

        audio = request.FILES["audio_file"]

        if not validate_audio_file(audio):
            return JsonResponse({"error": "نوع یا حجم فایل نامعتبر است."}, status=400)

        temp_path = get_temp_file_path(audio.name)

        with open(temp_path, "wb+") as f:
            for chunk in audio.chunks():
                f.write(chunk)
            f.flush()
            os.fsync(f.fileno())

        time.sleep(1.5)  # ✅ Ensure file is safely flushed to disk

        task = transcribe_audio.apply_async(args=[temp_path], countdown=2)

        return JsonResponse({"task_id": task.id}, status=202)

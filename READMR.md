### 📄 views.py

- مدیریت درخواست GET برای وضعیت تسک (state، progress، یا نتیجه نهایی).
- مدیریت فرم آپلود فایل صوتی از کاربر (POST).
- اعتبارسنجی نوع و اندازه فایل صوتی.
- ذخیره فایل به‌صورت موقت روی دیسک.
- ارسال فایل به Celery برای پردازش به‌صورت async با تأخیر ۲ ثانیه‌ای.
- استفاده از `AsyncResult` برای بررسی وضعیت پیشرفت یا خطا.


### 🧰 utils.py

- `delete_file(file_path)`: حذف فایل‌های موقتی ایجادشده پس از اتمام پردازش.
- `validate_audio_file(file)`: بررسی معتبر بودن نوع فایل صوتی (MIME type) و محدودیت حجم (تا ۵۰۰MB).
- `get_temp_file_path(filename)`: تولید مسیر یکتا برای ذخیره‌سازی موقت فایل‌ها در `media/whisper_temp`.
- `get_audio_duration_seconds(file_path)`: محاسبه مدت زمان فایل صوتی با استفاده از `pydub.utils.mediainfo`.


### 🧠 tasks.py

- `transcribe_audio`: وظیفه‌ی اصلی Celery برای تبدیل فایل صوتی به متن. پشتیبانی از:
  - تقسیم فایل‌های طولانی به قطعه‌های ۵ دقیقه‌ای (`split_audio`)
  - تشخیص زبان (پیش‌فرض `fa`)
  - مدیریت خطا و محدودیت زمانی (`SoftTimeLimitExceeded`)
  - ذخیره جزئیات متن در فایل `.partial.txt` پس از هر chunk
  - به‌روزرسانی وضعیت Celery (`update_state`) جهت نمایش درصد پیشرفت

- `split_audio(file_path, chunk_length_ms=300_000)`: تقسیم فایل به بخش‌های کوچکتر ۵ دقیقه‌ای با فرمت `.wav`.

- `get_audio_duration_seconds(file_path)`: محاسبه مدت زمان فایل با `pydub` برای تعیین long/short task.


### 📝 forms.py

- تعریف فرم `AudioUploadForm` برای آپلود فایل صوتی با استفاده از `forms.FileField`.
- اعمال `accept="audio/*"` در input جهت محدود کردن فایل‌های انتخابی به انواع صوتی.
- استفاده از ویجت `ClearableFileInput` برای امکان پاک‌کردن فایل انتخابی.


### ⚙️ apps.py

- پیکربندی اولیه اپلیکیشن `voice_to_text` در Django.
- مشخص کردن `default_auto_field` برای استفاده از کلیدهای خودکار نوع BigAutoField.
- متد `ready()` فعلاً خالی است ولی برای اتصال سیگنال‌ها در آینده قابل استفاده است.


### 🚀 celery.py

- راه‌اندازی Celery برای پروژه Django با نام `whisper_project`.
- بارگذاری تنظیمات مربوط به Celery از فایل `settings.py` با namespace = `CELERY`.
- فعال‌سازی auto-discover برای یافتن وظایف (tasks) از اپلیکیشن‌ها.
- پیکربندی پیش‌فرض مانند:
  - `task_time_limit`: محدودیت زمانی برای هر task (۱ ساعت)
  - `task_serializer`: فرمت json برای ارسال task
  - `task_default_queue`: صف پیش‌فرض برای اجرای تسک‌ها

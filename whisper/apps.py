from django.apps import AppConfig

class VoiceToTextConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'voice_to_text'

    def ready(self):
        # Place to import signals if needed
        pass
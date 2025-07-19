from django import forms

class AudioUploadForm(forms.Form):
    audio_file = forms.FileField(label='Select an audio file', widget=forms.ClearableFileInput(attrs={'accept': 'audio/*'}))

from django import forms

from dal import autocomplete

from .models import Fornitore, OffertaCommessa, Commessa


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(file_data, initial) for file_data in data]
        return [single_file_clean(data, initial)]


class ExcelUploadForm(forms.Form):
    file = MultipleFileField(
        label='File Excel o CSV',
        help_text='Carica uno o piu file .xlsx o .csv con i dati delle offerte/commesse.',
        widget=MultipleFileInput(attrs={
            'accept': '.xlsx,.csv',
            'class': 'upload-file-input',
            'multiple': True,
        }),
    )


class FornitoreForm(forms.ModelForm):
    class Meta:
        model = Fornitore
        fields = ('__all__')
        widgets = {
            'paese': autocomplete.ModelSelect2(url='comune-autocomplete'),
        }


class CommessaForm(forms.ModelForm):
    class Meta:
        model = Commessa
        fields = ['codice',
                  'produttore',
                  'is_done',
                  'garanzia_fin',
                  'tipologia',
                  'quantita',
                  'note',
                  'paese',
                  'latitudine',
                  'longitudine',
                  'is_commessa']
        widgets = {
            'paese': autocomplete.ModelSelect2(url='comune-autocomplete'),
        }


class OffertaCommessaForm(forms.ModelForm):
    class Meta:
        model = OffertaCommessa
        fields = ['codice',
                  'produttore',
                  'garanzia_fin',
                  'tipologia',
                  'quantita',
                  'note',
                  'paese',
                  'latitudine',
                  'longitudine',
                  'is_commessa']
        widgets = {
            'paese': autocomplete.ModelSelect2(url='comune-autocomplete'),
        }

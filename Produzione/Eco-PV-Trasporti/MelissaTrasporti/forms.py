from django import forms

from dal import autocomplete

from .models import Fornitore, OffertaCommessa, Commessa


class ExcelUploadForm(forms.Form):
    file = forms.FileField(
        label='File Excel o CSV',
        help_text='Carica un file .xlsx, .xls o .csv con i dati delle offerte/commesse.'
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

from django import forms

from dal import autocomplete

from .models import Commessa


class SelectTipoFornitori(forms.Form):
    trasporto = forms.BooleanField(label='Solo trasporto', required=False,)
    trattamento = forms.BooleanField(label='Solo trattamento', required=False,)
    completo = forms.BooleanField(label='Trasporto e Trattamento', required=False,)


class CommessaForm(forms.ModelForm):
    class Meta:
        model = Commessa
        fields = ('__all__')
        widgets = {
            'paese': autocomplete.ModelSelect2(url='comune-autocomplete')
        }
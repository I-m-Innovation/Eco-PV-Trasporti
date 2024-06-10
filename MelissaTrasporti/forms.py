from django import forms

from dal import autocomplete

from .models import Commessa,Offerta


class SelectTipoFornitori(forms.Form):
    trasporto = forms.BooleanField(label='Solo trasporto', required=False,)
    trattamento = forms.BooleanField(label='Solo trattamento', required=False,)
    completo = forms.BooleanField(label='Trasporto e Trattamento', required=False,)


class CommessaForm(forms.ModelForm):
    class Meta:
        model = Commessa
        fields = ('__all__')
        widgets = {
            'paese': autocomplete.ModelSelect2(url='comune-autocomplete'),
            'offerta': autocomplete.ModelSelect2(url='offerta-autocomplete')
        }


class OffertaForm(forms.ModelForm):
    class Meta:
        model = Offerta
        fields = ('__all__')
        widgets = {
            'paese': autocomplete.ModelSelect2(url='comune-autocomplete')
        }
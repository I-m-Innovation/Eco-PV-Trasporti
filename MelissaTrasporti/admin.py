from django.contrib import admin

from .models import Fornitore, Commessa, Offerta
from .forms import CommessaForm, OffertaForm


class FornitoreAdmin(admin.ModelAdmin):
    list_display = ('ragione_sociale', 'trasporto', 'trattamento', 'indirizzo')
    search_fields = ['ragione_sociale',]
    search_help_text = 'Cerca fornitore'


@admin.action(description="Contrassegna le commesse come effettuate")
def commessa_is_done(modeladmin, request, queryset):
    queryset.update(is_done=True)


class CommessaAdmin(admin.ModelAdmin):
    form = CommessaForm
    list_display = ('codice', 'produttore', 'is_done', 'garanzia_fin', 'tipologia', 'quantita', 'paese', 'latitudine', 'longitudine')
    list_filter = ('garanzia_fin', 'tipologia', 'is_done')
    search_fields = ['codice','produttore']
    search_help_text = 'Cerca commessa (inserire il codice)'
    actions = [commessa_is_done]


class OffertaAdmin(admin.ModelAdmin):
    form = OffertaForm
    list_display = ('codice', 'produttore', 'is_commessa', 'garanzia_fin', 'tipologia', 'quantita', 'paese', 'latitudine', 'longitudine')
    list_filter = ('garanzia_fin', 'tipologia',)
    search_fields = ['codice','produttore']
    search_help_text = 'Cerca offerta (inserire il codice)'


admin.site.register(Fornitore, FornitoreAdmin)
admin.site.register(Commessa, CommessaAdmin)
admin.site.register(Offerta, OffertaAdmin)






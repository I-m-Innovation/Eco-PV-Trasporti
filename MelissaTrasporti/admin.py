from django.contrib import admin

from .models import Fornitore, OffertaCommessa, Commessa
from .forms import CommessaForm, OffertaCommessaForm, FornitoreForm


class FornitoreAdmin(admin.ModelAdmin):
    form = FornitoreForm
    list_display = ('ragione_sociale', 'trasporto', 'trattamento', 'indirizzo', 'paese', 'latitudine', 'longitudine')
    search_fields = ['ragione_sociale',]
    search_help_text = 'Cerca fornitore'


@admin.action(description="Contrassegna come effettuate")
def commessa_is_done(modeladmin, request, queryset):
    queryset.update(is_done=True)


@admin.action(description="Trasforma in commessa")
def offerta_to_commessa(modeladmin, request, queryset):
    queryset.update(is_commessa=True)


class CommessaAdmin(admin.ModelAdmin):
    form = CommessaForm
    list_display = ('id','codice', 'produttore', 'is_done', 'garanzia_fin', 'tipologia', 'quantita', 'paese', 'note', 'latitudine', 'longitudine', )
    list_filter = ('garanzia_fin', 'tipologia', 'is_done')
    search_fields = ['codice','produttore']
    search_help_text = 'Cerca commessa (inserire il codice)'
    actions = [commessa_is_done]
    list_per_page = 50


class OffertaCommessaAdmin(admin.ModelAdmin):
    form = OffertaCommessaForm
    list_display = ('id','codice', 'produttore', 'is_commessa', 'garanzia_fin', 'tipologia', 'quantita', 'paese', 'note', 'latitudine', 'longitudine')
    list_filter = ('garanzia_fin', 'tipologia', 'is_commessa')
    search_fields = ['codice','produttore']
    search_help_text = 'Cerca offerta (inserire il codice)'
    actions = [offerta_to_commessa]
    list_per_page = 50


admin.site.register(Fornitore, FornitoreAdmin)
admin.site.register(Commessa, CommessaAdmin)
admin.site.register(OffertaCommessa, OffertaCommessaAdmin)






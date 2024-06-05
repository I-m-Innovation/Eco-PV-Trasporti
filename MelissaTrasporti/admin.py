from django.contrib import admin

from .models import Fornitore, Commessa
# from .models import Comune
from .forms import CommessaForm


admin.site.register(Fornitore)
# admin.site.register(Commessa)


class CommessaAdmin(admin.ModelAdmin):
    form = CommessaForm
    list_display = ('codice', 'produttore', 'garanzia_fin', 'tipologia', 'quantita', 'paese')
    list_filter = ('garanzia_fin', 'tipologia',)


admin.site.register(Commessa, CommessaAdmin)





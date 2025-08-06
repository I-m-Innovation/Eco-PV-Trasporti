from django.contrib import admin
from .models import RegistrationToken # Importa il nuovo modello

@admin.register(RegistrationToken)
class RegistrationTokenAdmin(admin.ModelAdmin):
    """Configurazione dell'interfaccia admin per i Token di Registrazione."""
    list_display = ('email', 'token', 'created_at', 'expires_at', 'is_used', 'user', 'is_valid_display')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'token', 'user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'expires_at', 'user', 'is_used') # Campi non modificabili direttamente qui

    # Azione personalizzata per marcare come usato (se necessario)
    # actions = ['mark_as_used']

    # Metodo per mostrare lo stato di validità nella lista
    def is_valid_display(self, obj):
        return obj.is_valid()
    is_valid_display.boolean = True # Mostra come icona (vero/falso)
    is_valid_display.short_description = "È Valido?" # Etichetta colonna

    # def mark_as_used(self, request, queryset):
    #     queryset.update(is_used=True)
    # mark_as_used.short_description = "Marca selezionati come Usati"

    # Sovrascriviamo i campi mostrati nel form di modifica/aggiunta
    # L'admin CREA un nuovo token inserendo solo l'email.
    # Il token e la scadenza vengono generati automaticamente.
    # L'admin NON modifica token esistenti da qui (sono read-only).
    def get_fields(self, request, obj=None):
        if obj: # Se stiamo modificando (visualizzando) un oggetto esistente
            return ('email', 'token', 'created_at', 'expires_at', 'is_used', 'user')
        else: # Se stiamo aggiungendo un nuovo oggetto
            return ('email',) # Chiediamo solo l'email per la creazione

    def get_readonly_fields(self, request, obj=None):
        if obj: # In modifica, rendi tutto read-only tranne forse l'email se vuoi permetterne la correzione
             return ('email', 'token', 'created_at', 'expires_at', 'is_used', 'user')
        else: # In aggiunta, nessun campo è read-only (ma mostriamo solo email)
            return ()

# Registra anche gli altri modelli se non l'hai già fatto
# from .models import Commessa, Offerta
# admin.site.register(Commessa)
# admin.site.register(Offerta)

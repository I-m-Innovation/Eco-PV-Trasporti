from django.db import models
from django.contrib.auth.models import User
import uuid # Per generare token univoci
from django.utils import timezone # Per gestire date e ore
from datetime import timedelta # Per calcolare la scadenza

class BaseModello(models.Model):
    """Classe base per i modelli Commessa e Offerta"""
    quantita = models.FloatField(verbose_name="Quantità")
    tipologia = models.CharField(max_length=100)
    produttore = models.CharField(max_length=200)
    indirizzo = models.CharField(max_length=255, verbose_name="Luogo di ritiro")
    provincia = models.CharField(max_length=50)
    data_ritiro = models.CharField(max_length=100, default="DA FARE")
    anno = models.IntegerField()
    latitudine = models.FloatField(null=True, blank=True)
    longitudine = models.FloatField(null=True, blank=True)
    
    class Meta:
        abstract = True

class Commessa(BaseModello):
    codice_commessa = models.CharField(max_length=100, unique=True)
    data_creazione = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Commessa {self.codice_commessa}"
    
    class Meta:
        verbose_name = "Commessa"
        verbose_name_plural = "Commesse"

class Offerta(BaseModello):
    codice_offerta = models.CharField(max_length=100, unique=True)
    codice_commessa = models.CharField(max_length=100, null=True, blank=True)
    data_offerta = models.DateField(null=True, blank=True)
    garanzia_finanziaria = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"Offerta {self.codice_offerta}"
    
    class Meta:
        verbose_name = "Offerta"
        verbose_name_plural = "Offerte"

class RegistrationToken(models.Model):
    """Modello per memorizzare i token di pre-registrazione."""
    email = models.EmailField(
        max_length=254,
        unique=True, # Assicura che ci sia solo un token attivo per email
        verbose_name="Email Richiedente"
    )
    token = models.UUIDField(
        default=uuid.uuid4, # Genera un UUID univoco automaticamente
        editable=False, # Non modificabile dall'admin (viene generato)
        unique=True,
        verbose_name="Token Univoco"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, # Imposta automaticamente alla creazione
        verbose_name="Data Creazione"
    )
    expires_at = models.DateTimeField(
        verbose_name="Data Scadenza"
    )
    is_used = models.BooleanField(
        default=False, # Il token non è stato ancora usato
        verbose_name="Utilizzato"
    )
    # Collega il token all'utente che si registra usandolo
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL, # Se l'utente viene cancellato, non cancellare il token, ma scollega
        null=True, # Permette che il campo sia vuoto (prima dell'uso)
        blank=True,
        related_name='registration_token',
        verbose_name="Utente Registrato"
    )

    def is_valid(self):
        """Controlla se il token è ancora valido (non usato e non scaduto)."""
        now = timezone.now()
        return not self.is_used and self.expires_at > now

    def save(self, *args, **kwargs):
        """Imposta la data di scadenza prima di salvare se non è già impostata."""
        if not self.expires_at:
            # Imposta la scadenza a 24 ore dalla creazione (puoi cambiarlo)
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs) # Chiama il metodo save originale

    def __str__(self):
        status = "Valido" if self.is_valid() else ("Usato" if self.is_used else "Scaduto")
        return f"Token per {self.email} ({status})"

    class Meta:
        verbose_name = "Token di Registrazione"
        verbose_name_plural = "Token di Registrazione"
        ordering = ['-created_at'] # Ordina i token dal più recente

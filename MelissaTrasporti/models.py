from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.db import models

from django.contrib.contenttypes.fields import GenericForeignKey


def check_localita(self):
	if not (self.paese or (self.latitudine and self.longitudine)):
		raise ValidationError({
			'paese': 'Inserire almeno un dato di posizione',
			'latitudine': 'Inserire almeno un dato di posizione',
			'longitudine': 'Inserire almeno un dato di posizione',
		})
	if self.longitudine:
		if not (-180 < self.longitudine < 180):
			raise ValidationError({'longitudine': 'Inserire un valore compreso tra -180 e 180'})
	if self.latitudine:
		if not (-90 < self.latitudine < 90):
			raise ValidationError({'latitudine': 'Inserire un valore compreso tra -90 e 90'})


class Comune(models.Model):
	cap = models.CharField(db_index=True, null=False, blank=False, validators=[RegexValidator('^[0-9]{5}$','Inserire CAP valido')], max_length=5 , editable=False)
	name = models.CharField(max_length=300, verbose_name="nome", editable=False)
	provincia = models.CharField(max_length=5, null=False, blank=False, db_index=True, editable=False)
	latitudine = models.FloatField(null=False, blank=False, editable=False)
	longitudine = models.FloatField(null=False, blank=False, editable=False)

	class Meta:
		ordering = ['name']
		verbose_name_plural = 'Località'
		verbose_name = 'Località'

	def __str__(self):
		return '%s, %s, %s' % (self.name, self.provincia, self.cap)


class Fornitore(models.Model):
	ragione_sociale = models.CharField(max_length=100, null=False, blank=False, verbose_name='Ragione Sociale')
	indirizzo = models.CharField(max_length=150, null=False, blank=False, verbose_name='Indirizzo')
	trasporto = models.BooleanField(verbose_name='Trasporto')
	trattamento = models.BooleanField(verbose_name='Trattamento')
	paese = models.ForeignKey(Comune, on_delete=models.PROTECT, help_text='CAP - Luogo di ritiro', verbose_name='Località', null=True, blank=True)
	latitudine = models.FloatField(null=True, blank=True)
	longitudine = models.FloatField(null=True, blank=True)

	def clean(self):
		check_localita(self)

	class Meta:
		verbose_name_plural = 'fornitori'
		ordering = ['ragione_sociale']

	def __str__(self):
		return self.ragione_sociale


scelta_garanzia = [('-','-'), ('ANTE','ANTE'), ('REM/ERION','REM/ERION')]


class OffertaCommessa(models.Model):
	codice = models.CharField(max_length=20, help_text='Codice identificativo', db_index=True, verbose_name='codice', unique=True)
	produttore = models.CharField(max_length=200, null=False, blank=False, help_text='Produttore del rifiuto')
	garanzia_fin = models.CharField(choices=scelta_garanzia, max_length=20, default='-', help_text='Garanzia finanziaria', verbose_name='garanzia finanziaria')
	quantita = models.IntegerField(null=False, blank=False, help_text='Quantità totale di rifiuti', verbose_name='quantità')
	tipologia = models.CharField(null=False, blank=False, verbose_name='tipologia', help_text='Tipologia di RAEE', max_length=250)
	note = models.TextField(null=True, blank=True, verbose_name='note', help_text='Info aggiuntive')
	paese = models.ForeignKey(Comune, on_delete=models.PROTECT, help_text='CAP - Luogo di ritiro', verbose_name='Località', null=True, blank=True)
	latitudine = models.FloatField(null=True, blank=True,)
	longitudine = models.FloatField(null=True, blank=True,)
	is_commessa = models.BooleanField(null=False, blank=False, default=False, verbose_name='check commessa', help_text='Identifica la pratica come "commessa"')
	is_done = models.BooleanField(null=False, blank=False, default=False, verbose_name='commessa evasa', help_text='Indica se la commessa è stata evasa')

	def clean(self):
		check_localita(self)

	class Meta:
		verbose_name_plural = 'offerte - commesse'
		ordering = ['codice']
		verbose_name = 'offerta - commessa'

	def __str__(self):
		if self.paese:
			return '%s, %s, %s' % (self.codice, self.produttore, self.paese)
		else:
			return '%s, %s' % (self.codice, self.produttore)


class CommessaManager(models.Manager):
	def get_queryset(self):
		return super(CommessaManager, self).get_queryset().filter(is_commessa=True)


class Commessa(OffertaCommessa):
	objects = CommessaManager()
	class Meta:
		proxy = True
		verbose_name_plural = 'commesse'
		ordering = ['codice']
		verbose_name = 'commessa'

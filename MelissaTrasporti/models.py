from django.core.validators import RegexValidator
from django.db import models

from django.contrib.contenttypes.fields import GenericForeignKey


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
	latitudine = models.FloatField(null=False, blank=False)
	longitudine = models.FloatField(null=False, blank=False)

	class Meta:
		verbose_name_plural = 'fornitori'
		ordering = ['ragione_sociale']

	def __str__(self):
		return self.ragione_sociale

scelta_garanzia = [('ANTE','ANTE'), ('-','-')]


class Offerta(models.Model):
	codice = models.CharField(max_length=20, help_text='Codice identificativo offerta', primary_key=True, verbose_name='codice offerta')
	produttore = models.CharField(max_length=200, null=False, blank=False, help_text='Produttore del rifiuto')
	garanzia_fin = models.CharField(choices=scelta_garanzia, max_length=20, default='-', help_text='Garanzia finanziaria', verbose_name='garanzia finanziaria')
	quantita = models.IntegerField(null=False, blank=False, help_text='Quantità totale di rifiuti', verbose_name='quantità')
	tipologia = models.TextField(null=False, blank=False, verbose_name='tipologia', help_text='Tipologia di RAEE')
	is_commessa = models.BooleanField(null=False, blank=False, default=False, verbose_name='commessa')
	paese = models.ForeignKey(Comune, on_delete=models.PROTECT, help_text='CAP - Luogo di ritiro', verbose_name='Località')
	latitudine = models.FloatField(null=True, blank=True, default=None)
	longitudine = models.FloatField(null=True, blank=True, default=None)

	class Meta:
		verbose_name_plural = 'offerte'
		ordering = ['codice']

	def __str__(self):
		return '%s, %s, %s' % (self.codice, self.produttore, self.paese)

class Commessa(models.Model):
	codice = models.CharField(max_length=20, help_text='Codice identificativo commessa', primary_key=True, verbose_name='codice commessa')
	offerta = models.ForeignKey(Offerta, on_delete=models.PROTECT, verbose_name='offerta di riferimento', blank=True, null=True)
	produttore = models.CharField(max_length=200, null=False, blank=False, help_text='Produttore del rifiuto')
	is_done = models.BooleanField(null=False, blank=False, default=False, verbose_name='commessa eseguita')
	garanzia_fin = models.CharField(choices=scelta_garanzia, max_length=20, default='-',help_text='Garanzia finanziaria', verbose_name='garanzia finanziaria')
	quantita = models.IntegerField(null=False, blank=False, help_text='Quantità totale di rifiuti', verbose_name='quantità')
	tipologia = models.TextField(null=False, blank=False, verbose_name='tipologia', help_text='Tipologia di RAEE')
	paese = models.ForeignKey(Comune, on_delete=models.PROTECT, help_text='CAP - Luogo di ritiro', verbose_name='Località')
	latitudine = models.FloatField(null=True, blank=True, default=None)
	longitudine = models.FloatField(null=True, blank=True, default=None)

	class Meta:
		verbose_name_plural = 'commesse'
		ordering = ['is_done', 'codice']

	def __str__(self):
		return self.codice

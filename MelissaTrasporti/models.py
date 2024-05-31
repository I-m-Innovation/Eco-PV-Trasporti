from django.db import models


class Fornitore(models.Model):
	ragione_sociale = models.CharField(max_length=100)
	indirizzo = models.CharField(max_length=150)
	trasporto = models.BooleanField()
	trattamento = models.BooleanField()
	latitudine = models.FloatField()
	longitudine = models.FloatField()

	class Meta:
		verbose_name_plural = 'Fornitori'

	def __str__(self):
		return self.ragione_sociale
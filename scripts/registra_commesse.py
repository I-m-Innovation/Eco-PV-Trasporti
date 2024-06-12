import pandas as pd
from django.conf import settings
from MelissaTrasporti.models import OffertaCommessa


if __name__=='__main__':
	data_file = settings.BASE_DIR / 'backups' / ''
	DF = pd.read_csv(data_file, sep='\t')
	columns = ['codice', 'produttore', 'garanzia_fin', 'quantita', 'tipologia', 'note', 'paese', 'latitudine', 'longitudine', 'offerta_commessa', 'is_done']
	DF = DF[columns]

	records = []
	for index, row in DF.iterrows():
		records.append({key: row[key] for key in columns})

	for record in records:
		OffertaCommessa.objects.create(
			codice=record['codice'],
			produttore=record['produttore'],
			garanzia_fin=record['garanzia_fin'],
			quantita=record['quantita'],
			tipologia=record['tipologia'],
			note=record['note'],
			paese=record['paese'],
			latitudine=record['latitudine'],
			longitudine=record['longitudine'],
			offerta_commessa=record['offerta_commessa'],
			is_done=record['is_done']
		)
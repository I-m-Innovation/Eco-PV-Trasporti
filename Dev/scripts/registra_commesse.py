import pandas as pd
from django.conf import settings
from MelissaTrasporti.models import *


if __name__=='__main__':
	data_file = settings.BASE_DIR / 'backups' / 'DumpedData_28-08-2024T14-24-34.csv'
	DF = pd.read_csv(data_file, sep=',')
	columns = ['codice', 'produttore', 'garanzia_fin', 'quantita', 'tipologia', 'note', 'paese', 'latitudine', 'longitudine', 'is_commessa', 'is_done']
	DF = DF[columns]
	DF['note'] = DF['note'].fillna('-')
	records = []

	for index, row in DF.iterrows():
		records.append(
			OffertaCommessa(
				codice=row['codice'],
				produttore=row['produttore'],
				garanzia_fin=row['garanzia_fin'],
				quantita=row['quantita'],
				tipologia=row['tipologia'],
				note=row['note'],
				paese=Comune.objects.get(id=row['paese']),
				latitudine=row['latitudine'],
				longitudine=row['longitudine'],
				is_commessa=row['is_commessa'],
				is_done=row['is_done']
			)
		)

	OffertaCommessa.objects.bulk_create(records)
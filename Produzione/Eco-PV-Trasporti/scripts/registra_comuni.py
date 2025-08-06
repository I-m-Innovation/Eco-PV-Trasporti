import pandas as pd
from django.conf import settings
from MelissaTrasporti.models import Comune


if __name__=='__main__':
	data_file = settings.BASE_DIR / 'data' / 'comuni_italiani.csv'
	DF = pd.read_csv(data_file,sep=';')
	columns = ['cap', 'denominazione_ita', 'sigla_provincia', 'lat', 'lon',]
	DF = DF[columns]
	DF['lon'] = DF['lon'].str.replace(',', '.').astype('float')
	DF['lat'] = DF['lat'].str.replace(',', '.').astype('float')
	DF['cap'] = DF['cap'].astype('string')

	records = []
	for index, row in DF.iterrows():
		records.append({key: row[key] for key in columns})

	Comune.objects.all().delete()
	for record in records:
		Comune.objects.create(
			cap=record['cap'],
			name=record['denominazione_ita'],
			provincia=record['sigla_provincia'],
			latitudine=record['lat'],
			longitudine=record['lon']
		)
import pandas as pd
from django.conf import settings
from MelissaTrasporti.models import Fornitore


if __name__=='__main__':
	data_file = settings.BASE_DIR / 'data' / 'Elenco_Fornitori_Clienti.xlsx'
	DF = pd.read_excel(data_file, sheet_name='FORNITORI', skiprows=2)
	columns = ['RAGIONE SOCIALE', 'TRASPORTO', 'TRATTAMENTO', 'SEDE INDIRIZZO', 'LATITUDINE', 'LONGITUDINE']
	DF = DF[columns]
	DF.fillna('-', inplace=True)

	records = []
	for index, row in DF.iterrows():
		records.append({key: row[key] for key in columns})

	for record in records:
		Fornitore.objects.get_or_create(
			ragione_sociale=record['RAGIONE SOCIALE'],
			indirizzo=record['SEDE INDIRIZZO'],
			trasporto=record['TRASPORTO'] != '-',
			trattamento=record['TRATTAMENTO'] != '-',
			latitudine=record['LATITUDINE'],
			longitudine=record['LONGITUDINE']
		)
from datetime import datetime

import os
from django.conf import settings

from MelissaTrasporti.models import OffertaCommessa
import pandas as pd

if __name__=='__main__':
	data = list(OffertaCommessa.objects.filter(is_done=False).values(
		'codice',
		'produttore',
		'garanzia_fin',
		'quantita',
		'tipologia',
		'note',
		'latitudine',
		'longitudine',
		'paese',
		'is_commessa',
		'is_done'
	))

	DF = pd.DataFrame(data)
	now = datetime.now()
	now = now.strftime("%d-%m-%YT%H-%M-%S")
	path = settings.BASE_DIR / 'backups' / 'DumpedData_{dt}.csv'.format(dt=now)

	DF.to_csv(path, sep=',', index=False)

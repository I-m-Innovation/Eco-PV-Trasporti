# Generated by Django 4.2.13 on 2024-06-04 13:49

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comune',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cap', models.CharField(db_index=True, editable=False, max_length=5, validators=[django.core.validators.RegexValidator('^[0-9]{5}$', 'Inserire CAP valido')])),
                ('name', models.CharField(editable=False, max_length=300, verbose_name='nome')),
                ('provincia', models.CharField(db_index=True, editable=False, max_length=5)),
                ('latitudine', models.FloatField(editable=False)),
                ('longitudine', models.FloatField(editable=False)),
            ],
            options={
                'verbose_name_plural': 'comuni',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Fornitore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ragione_sociale', models.CharField(max_length=100, verbose_name='Ragione Sociale')),
                ('indirizzo', models.CharField(max_length=150, verbose_name='Indirizzo')),
                ('trasporto', models.BooleanField(verbose_name='Trasporto')),
                ('trattamento', models.BooleanField(verbose_name='Trattamento')),
                ('latitudine', models.FloatField()),
                ('longitudine', models.FloatField()),
            ],
            options={
                'verbose_name_plural': 'fornitori',
                'ordering': ['ragione_sociale'],
            },
        ),
        migrations.CreateModel(
            name='Commessa',
            fields=[
                ('codice', models.CharField(help_text='Codice identificativo commessa', max_length=20, primary_key=True, serialize=False, verbose_name='codice commessa')),
                ('produttore', models.CharField(help_text='Produttore del rifiuto', max_length=200)),
                ('garanzia_fin', models.CharField(choices=[('ANTE', 'ANTE'), ('-', '-')], default='-', help_text='Garanzia finanziaria', max_length=20, verbose_name='garanzia finanziaria')),
                ('quantita', models.IntegerField(help_text='Quantità totale di rifiuti', verbose_name='quantità')),
                ('tipologia', models.CharField(help_text='Tipologia dei rifiuti', max_length=30)),
                ('paese', models.ForeignKey(help_text='CAP - Luogo di ritiro', on_delete=django.db.models.deletion.PROTECT, to='MelissaTrasporti.comune')),
            ],
            options={
                'verbose_name_plural': 'commesse',
                'ordering': ['codice'],
            },
        ),
    ]

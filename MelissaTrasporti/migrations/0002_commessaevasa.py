# Generated by Django 4.2.13 on 2024-08-29 16:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('MelissaTrasporti', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommessaEvasa',
            fields=[
            ],
            options={
                'verbose_name': 'commessa evasa',
                'verbose_name_plural': 'commesse evase',
                'ordering': ['codice'],
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('MelissaTrasporti.offertacommessa',),
        ),
    ]
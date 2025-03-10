# Generated by Django 4.0.4 on 2022-06-21 12:59

import datetime
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GeoFence',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('raw_geo_fence', models.TextField(blank=True, help_text='Set a GeoJSON as a GeoFence', null=True)),
                ('geozone', models.TextField(blank=True, help_text='Set a ED-269 Compliant GeoZone', null=True)),
                ('upper_limit', models.DecimalField(decimal_places=2, max_digits=6)),
                ('lower_limit', models.DecimalField(decimal_places=2, max_digits=6)),
                ('altitude_ref', models.IntegerField(choices=[(0, 'WGS84'), (1, 'AGL'), (2, 'MSL')], default=0)),
                ('name', models.CharField(max_length=50)),
                ('bounds', models.CharField(max_length=140)),
                ('start_datetime', models.DateTimeField(default=datetime.datetime.now)),
                ('end_datetime', models.DateTimeField(default=datetime.datetime.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

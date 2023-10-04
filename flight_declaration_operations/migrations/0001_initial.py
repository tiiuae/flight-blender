# Generated by Django 4.0.4 on 2022-06-23 10:49

import datetime
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FlightDeclaration",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("operational_intent", models.JSONField()),
                (
                    "flight_declaration_raw_geojson",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "type_of_operation",
                    models.IntegerField(
                        choices=[(0, "VLOS"), (1, "BVLOS")],
                        default=0,
                        help_text="At the moment, only VLOS and BVLOS operations are supported, for other types of operations, please issue a pull-request",
                    ),
                ),
                ("bounds", models.CharField(max_length=140)),
                (
                    "originating_party",
                    models.CharField(
                        default="Flight Blender Default",
                        help_text="Set the party originating this flight, you can add details e.g. Aerobridge Flight 105",
                        max_length=100,
                    ),
                ),
                (
                    "submitted_by",
                    models.EmailField(blank=True, max_length=254, null=True),
                ),
                (
                    "approved_by",
                    models.EmailField(blank=True, max_length=254, null=True),
                ),
                ("start_datetime", models.DateTimeField(default=datetime.datetime.now)),
                ("end_datetime", models.DateTimeField(default=datetime.datetime.now)),
                ("is_approved", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]

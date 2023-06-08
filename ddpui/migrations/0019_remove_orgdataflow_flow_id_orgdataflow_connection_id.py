# Generated by Django 4.1.7 on 2023-06-01 14:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ddpui", "0018_orgdataflow_deployment_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="orgdataflow",
            name="flow_id",
        ),
        migrations.AddField(
            model_name="orgdataflow",
            name="connection_id",
            field=models.CharField(max_length=36, null=True, unique=True),
        ),
    ]
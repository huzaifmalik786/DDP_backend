# Generated by Django 4.1.7 on 2023-05-18 14:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ddpui", "0017_alter_orgdataflow_cron"),
    ]

    operations = [
        migrations.AddField(
            model_name="orgdataflow",
            name="deployment_name",
            field=models.CharField(max_length=100, null=True),
        ),
    ]
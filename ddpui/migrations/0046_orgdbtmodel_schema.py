# Generated by Django 4.1.7 on 2024-02-14 10:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ddpui", "0045_orgdbtmodel"),
    ]

    operations = [
        migrations.AddField(
            model_name="orgdbtmodel",
            name="schema",
            field=models.CharField(max_length=100, null=True),
        ),
    ]

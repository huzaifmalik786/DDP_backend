# Generated by Django 4.1.7 on 2023-12-23 02:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ddpui", "0036_orgtnc"),
    ]

    operations = [
        migrations.AddField(
            model_name="userattributes",
            name="is_consultant",
            field=models.BooleanField(default=False),
        ),
    ]
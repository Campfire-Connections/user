# Generated by Django 5.0.6 on 2024-12-07 01:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0012_user_is_new_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="slug",
            field=models.SlugField(blank=True, max_length=255),
        ),
    ]

# Generated by Django 4.0.6 on 2022-08-08 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitemap', '0017_rename_operation_page_betweenstepoperation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='possibleValues',
            field=models.TextField(null=True),
        ),
    ]

# Generated by Django 4.0.6 on 2022-08-05 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitemap', '0015_alter_option_maximum_alter_option_minimum_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='attribute',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='option',
            name='geoFile',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='operation',
            field=models.TextField(null=True),
        ),
    ]

# Generated by Django 3.0.8 on 2020-07-06 03:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('igstatsapp', '0006_edmdata_total_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='edmdata',
            name='recipient_email',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]

# Generated by Django 3.0.8 on 2020-07-04 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('igstatsapp', '0004_auto_20200704_0824'),
    ]

    operations = [
        migrations.CreateModel(
            name='CsvData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=5, null=True)),
                ('domain', models.CharField(max_length=100)),
                ('campaign_id', models.CharField(max_length=100)),
                ('recipient', models.CharField(max_length=100)),
                ('clicked', models.PositiveIntegerField()),
                ('opened', models.PositiveIntegerField()),
                ('delivered', models.PositiveIntegerField()),
                ('bounced', models.PositiveIntegerField()),
                ('complained', models.PositiveIntegerField()),
                ('unsubscribed', models.PositiveIntegerField()),
                ('trans_date', models.DateTimeField()),
            ],
        ),
    ]

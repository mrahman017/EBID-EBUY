# Generated by Django 4.2.1 on 2022-12-09 09:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0003_auction_current_bid'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='comment',
            new_name='message',
        ),
    ]

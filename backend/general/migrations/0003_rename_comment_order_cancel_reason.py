# Generated by Django 5.2.1 on 2025-06-08 18:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0002_order_comment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='comment',
            new_name='cancel_reason',
        ),
    ]

# Generated manually to fix missing attachment field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_alter_ticket_options_remove_ticketreply_reply_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketreply',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='ticket_attachments/'),
        ),
    ]



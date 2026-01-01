# Generated migration to handle Client.company data conversion

from django.db import migrations, connection


def migrate_client_company_data(apps, schema_editor):
    """Convert Client.company CharField to ForeignKey"""
    Client = apps.get_model('core', 'Client')
    Company = apps.get_model('core', 'Company')
    
    # Get or create default company
    default_company, _ = Company.objects.get_or_create(
        slug='default-company',
        defaults={
            'name': 'Default Company',
            'description': 'Default company for existing data',
            'is_active': True
        }
    )
    
    # Update all clients to use default company
    # Since the old company field was CharField and we're converting to ForeignKey,
    # we'll assign all existing clients to the default company
    Client.objects.filter(company_new__isnull=True).update(company_new=default_company)


def reverse_migrate_client_company_data(apps, schema_editor):
    """Reverse migration - set company_new to None"""
    Client = apps.get_model('core', 'Client')
    Client.objects.all().update(company_new=None)


def drop_old_company_field(apps, schema_editor):
    """Drop old company CharField if it exists"""
    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'core_client' 
            AND COLUMN_NAME = 'company' 
            AND DATA_TYPE = 'varchar'
        """)
        if cursor.fetchone()[0] > 0:
            try:
                cursor.execute("ALTER TABLE core_client DROP COLUMN company")
            except Exception:
                pass  # Column might not exist or already dropped


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_alter_asset_asset_id_alter_budgetcategory_name_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_client_company_data, reverse_migrate_client_company_data),
        migrations.RunPython(drop_old_company_field, migrations.RunPython.noop),
        migrations.RenameField(
            model_name='client',
            old_name='company_new',
            new_name='company',
        ),
    ]

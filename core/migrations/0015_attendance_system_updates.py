# Generated manually for attendance system updates

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_employee_can_view_attendance_and_more'),
    ]

    operations = [
        # Add new fields to Employee model
        migrations.AddField(
            model_name='employee',
            name='machine_id',
            field=models.CharField(blank=True, help_text='Employee ID registered in the ZKT machine', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='fingerprint_id',
            field=models.CharField(blank=True, help_text='Fingerprint ID in the ZKT machine', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='face_id',
            field=models.CharField(blank=True, help_text='Face ID in the ZKT machine', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='card_id',
            field=models.CharField(blank=True, help_text='Card ID in the ZKT machine', max_length=50, null=True),
        ),
        
        # Create AttendanceMachine model
        migrations.CreateModel(
            name='AttendanceMachine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='ZKT K70', max_length=100)),
                ('ip_address', models.GenericIPAddressField(default='192.168.18.1')),
                ('port', models.IntegerField(default=4370)),
                ('location', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        
        # Create AttendanceLog model
        migrations.CreateModel(
            name='AttendanceLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attendance_type', models.CharField(choices=[('check_in', 'Check In'), ('check_out', 'Check Out'), ('break_start', 'Break Start'), ('break_end', 'Break End')], max_length=20)),
                ('source', models.CharField(choices=[('manual', 'Manual'), ('machine', 'ZKT Machine'), ('api', 'API')], default='manual', max_length=10)),
                ('timestamp', models.DateTimeField()),
                ('machine_timestamp', models.DateTimeField(blank=True, help_text='Original timestamp from the machine', null=True)),
                ('machine_id', models.CharField(blank=True, help_text='Machine ID if from ZKT device', max_length=50, null=True)),
                ('location', models.CharField(blank=True, max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_logs', to='core.employee')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes to AttendanceLog
        migrations.AddIndex(
            model_name='attendancelog',
            index=models.Index(fields=['employee', 'timestamp'], name='core_attendance_employee_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='attendancelog',
            index=models.Index(fields=['timestamp'], name='core_attendance_timestamp_123456_idx'),
        ),
        
        # Update Attendance model
        migrations.RenameField(
            model_name='attendance',
            old_name='user',
            new_name='employee',
        ),
        migrations.AlterField(
            model_name='attendance',
            name='check_in',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='check_out',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendance',
            name='break_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendance',
            name='break_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendance',
            name='total_work_hours',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='attendance',
            name='total_break_hours',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='status',
            field=models.CharField(choices=[('present', 'Present'), ('absent', 'Absent'), ('late', 'Late'), ('half_day', 'Half Day'), ('holiday', 'Holiday'), ('leave', 'Leave')], default='present', max_length=20),
        ),
        migrations.AddField(
            model_name='attendance',
            name='is_late',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attendance',
            name='late_minutes',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='attendance',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('employee', 'date')},
        ),
        migrations.AlterModelOptions(
            name='attendance',
            options={'ordering': ['-date']},
        ),
    ]

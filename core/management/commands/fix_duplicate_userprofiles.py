from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
from django.db.models import Count


class Command(BaseCommand):
    help = 'Fix duplicate UserProfile entries by keeping the first one and deleting duplicates'

    def handle(self, *args, **options):
        # Find users with duplicate profiles
        duplicates = UserProfile.objects.values('user_id').annotate(
            count=Count('user_id')
        ).filter(count__gt=1)
        
        fixed_count = 0
        for dup in duplicates:
            user_id = dup['user_id']
            profiles = UserProfile.objects.filter(user_id=user_id).order_by('id')
            
            if profiles.count() > 1:
                # Keep the first one, delete the rest
                first_profile = profiles.first()
                duplicates_to_delete = profiles.exclude(id=first_profile.id)
                
                self.stdout.write(
                    f"User ID {user_id} has {profiles.count()} profiles. "
                    f"Keeping profile ID {first_profile.id}, deleting {duplicates_to_delete.count()} duplicates."
                )
                
                # Update the first profile with data from duplicates if needed
                for dup_profile in duplicates_to_delete:
                    if dup_profile.company and not first_profile.company:
                        first_profile.company = dup_profile.company
                    if dup_profile.is_company_admin and not first_profile.is_company_admin:
                        first_profile.is_company_admin = dup_profile.is_company_admin
                    first_profile.save()
                
                duplicates_to_delete.delete()
                fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {fixed_count} duplicate UserProfile entries.')
            )
        else:
            self.stdout.write(self.style.SUCCESS('No duplicate UserProfile entries found.'))


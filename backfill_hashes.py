import os
import django
import imagehash
from PIL import Image

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'civicwaste.settings')
django.setup()

from reports.models import WasteReport

print("Backfilling image hashes for existing reports...")
reports = WasteReport.objects.exclude(photo__exact='')

updated = 0
for report in reports:
    try:
        # Check if hash is already in description
        if '[HASH:' in getattr(report, 'description', ''):
            continue
            
        if getattr(report, 'photo', None) and getattr(report.photo, 'file', None):
            img = Image.open(report.photo.file)
            h = str(imagehash.average_hash(img))
            
            # Append hash
            report.description = f"{getattr(report, 'description', '')}\n[HASH:{h}]"
            report.save(update_fields=['description'])
            updated += 1
            print(f"Updated report #{report.id} with hash {h}")
    except Exception as e:
        print(f"Failed to process report #{report.id}: {e}")

print(f"Backfill complete. Updated {updated} reports.")

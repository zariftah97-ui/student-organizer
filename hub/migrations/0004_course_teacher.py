from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('hub', '0003_academic_foundation')]
    operations = [migrations.AddField(model_name='course', name='teacher', field=models.CharField(blank=True, max_length=160))]

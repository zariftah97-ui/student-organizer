from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('hub', '0004_course_teacher')]
    operations = [migrations.AlterField(model_name='userpreference', name='theme', field=models.CharField(choices=[('light', 'Sage Garden'), ('dark', 'Deep Garden')], default='light', max_length=10))]

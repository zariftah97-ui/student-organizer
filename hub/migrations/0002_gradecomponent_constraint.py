from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('hub', '0001_initial')]

    operations = [
        migrations.AlterUniqueTogether(
            name='gradecomponent',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='gradecomponent',
            constraint=models.UniqueConstraint(
                fields=('course', 'label'),
                name='unique_grade_component_per_course',
            ),
        ),
    ]

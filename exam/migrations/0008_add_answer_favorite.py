from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0007_alter_practicequestion_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='is_favorited',
            field=models.BooleanField(default=False, verbose_name='是否收藏'),
        ),
    ]


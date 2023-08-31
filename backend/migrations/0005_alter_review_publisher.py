# Generated by Django 4.2.1 on 2023-06-10 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0004_alter_publisher_platforms"),
    ]

    operations = [
        migrations.AlterField(
            model_name="review",
            name="publisher",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reviews",
                related_query_name="review",
                to="backend.publisher",
            ),
        ),
    ]
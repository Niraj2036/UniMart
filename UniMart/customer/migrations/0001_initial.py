# Generated by Django 5.0.6 on 2024-06-13 19:17

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("mobile_number", models.CharField(max_length=15)),
                (
                    "role",
                    models.CharField(
                        choices=[("customer", "Customer"), ("seller", "Seller")],
                        default="user",
                        max_length=10,
                    ),
                ),
                ("address", models.TextField(blank=True)),
                ("shop_name", models.CharField(blank=True, max_length=255)),
                ("shop_logo_url", models.URLField(blank=True)),
                ("shop_catagory", models.TextField(blank=True)),
            ],
        ),
    ]
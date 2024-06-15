from django.db import migrations

def delete_data(apps, schema_editor):
    # Access the models
    Customer = apps.get_model('customer', 'Customer')
    Product = apps.get_model('customer', 'Product')
    Order = apps.get_model('customer', 'Order')

    # Delete all instances
    Customer.objects.all().delete()
    Product.objects.all().delete()
    Order.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0003_order'),  # Ensure it matches your previous migration
    ]

    operations = [
        migrations.RunPython(delete_data),
    ]

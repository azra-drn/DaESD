from django.db import migrations, models


OFFICIAL_ALLERGENS = [
    "Celery",
    "Cereals containing gluten",
    "Crustaceans",
    "Eggs",
    "Fish",
    "Lupin",
    "Milk",
    "Molluscs",
    "Mustard",
    "Peanuts",
    "Sesame",
    "Soybeans",
    "Sulphur dioxide / sulphites",
    "Tree nuts",
]


def refresh_allergens(apps, schema_editor):
    Allergen = apps.get_model("catalog", "Allergen")
    Product = apps.get_model("catalog", "Product")

    rename_map = {
        "Gluten": "Cereals containing gluten",
        "Nuts": "Tree nuts",
    }

    for old_name, new_name in rename_map.items():
        try:
            old_allergen = Allergen.objects.get(name=old_name)
        except Allergen.DoesNotExist:
            old_allergen = None

        if not old_allergen:
            continue

        replacement, _ = Allergen.objects.get_or_create(name=new_name)
        linked_products = Product.objects.filter(allergens=old_allergen)
        for product in linked_products:
            product.allergens.add(replacement)
        old_allergen.delete()

    for name in OFFICIAL_ALLERGENS:
        Allergen.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0008_product_low_stock_threshold"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="season_months",
            field=models.CharField(
                blank=True,
                help_text="Optional season window such as June-August for in-season products.",
                max_length=80,
            ),
        ),
        migrations.RunPython(refresh_allergens, migrations.RunPython.noop),
    ]

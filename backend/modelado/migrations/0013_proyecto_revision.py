from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("modelado", "0012_atributo_es_estatico_atributo_tipo_referencia_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="proyecto",
            name="revision",
            field=models.PositiveBigIntegerField(
                default=0,
                help_text="Revisión monotónica del estado UML confirmado del proyecto.",
            ),
        ),
    ]

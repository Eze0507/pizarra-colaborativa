from rest_framework import serializers


class StrictNonNegativeIntegerField(serializers.Field):
    default_error_messages = {
        "invalid": "Este campo debe ser un entero no negativo.",
    }

    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, int) or data < 0:
            self.fail("invalid")
        return data

    def to_representation(self, value):
        return value


class StrictBooleanField(serializers.Field):
    default_error_messages = {"invalid": "Este campo debe ser booleano."}

    def to_internal_value(self, data):
        if not isinstance(data, bool):
            self.fail("invalid")
        return data

    def to_representation(self, value):
        return value


class SpringBootOptionsSerializer(serializers.Serializer):
    modelo = StrictBooleanField(required=True)
    repositorio = StrictBooleanField(required=True)
    servicio = StrictBooleanField(required=True)
    controlador = StrictBooleanField(required=True)

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Este campo debe ser un objeto.")
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({
                "opciones_desconocidas": sorted(unknown),
            })
        return super().to_internal_value(data)

    def validate(self, attrs):
        dependencies = (
            ("repositorio", "modelo"),
            ("servicio", "repositorio"),
            ("controlador", "servicio"),
        )
        invalid = [
            {"opcion": option, "requiere": dependency}
            for option, dependency in dependencies
            if attrs.get(option) and not attrs.get(dependency)
        ]
        if invalid:
            raise serializers.ValidationError({
                "codigo": "CRUD_INVALID_OPTION_COMBINATION",
                "dependencias": invalid,
            })
        return attrs


class GenerarSpringBootSerializer(serializers.Serializer):
    expected_revision = StrictNonNegativeIntegerField(required=True)
    nombre_proyecto = serializers.CharField(
        required=True, allow_blank=False, trim_whitespace=False, max_length=64
    )
    paquete_base = serializers.CharField(
        required=True, allow_blank=False, trim_whitespace=False, max_length=200
    )
    opciones = SpringBootOptionsSerializer(required=True)

    def validate(self, attrs):
        unknown = set(self.initial_data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({
                "campos_desconocidos": sorted(unknown),
            })
        return attrs


class ImportarXMLSerializer(serializers.Serializer):
    """
    Serializer para la importación de archivos XML 2.1 (XMI 2.1) de Enterprise Architect.
    Permite cargar el archivo directamente mediante multipart/form-data o enviar el texto XML plano.
    """
    archivo_xml = serializers.FileField(required=False, allow_null=True)
    contenido_xml = serializers.CharField(required=False, allow_blank=True)
    reemplazar_existente = serializers.BooleanField(default=True, required=False)
    expected_revision = serializers.IntegerField(min_value=0, required=True)

    def validate(self, attrs):
        archivo = attrs.get('archivo_xml')
        contenido = attrs.get('contenido_xml', '').strip()

        if not archivo and not contenido:
            raise serializers.ValidationError(
                "Debe proporcionar un archivo XML en 'archivo_xml' o el texto XML en 'contenido_xml'."
            )

        if archivo:
            # Validar tamaño máximo (10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    "El archivo supera el tamaño máximo permitido de 10 MB."
                )
            try:
                raw_bytes = archivo.read()
                try:
                    contenido_decodificado = raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    contenido_decodificado = raw_bytes.decode('windows-1252', errors='replace')
                attrs['contenido_xml'] = contenido_decodificado
            except Exception as e:
                raise serializers.ValidationError(
                    f"Error al leer el archivo XML: {str(e)}"
                )

        return attrs

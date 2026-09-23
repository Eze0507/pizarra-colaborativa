from rest_framework import serializers


class ImportarXMLSerializer(serializers.Serializer):
    """
    Serializer para la importación de archivos XML 2.1 (XMI 2.1) de Enterprise Architect.
    Permite cargar el archivo directamente mediante multipart/form-data o enviar el texto XML plano.
    """
    archivo_xml = serializers.FileField(required=False, allow_null=True)
    contenido_xml = serializers.CharField(required=False, allow_blank=True)
    reemplazar_existente = serializers.BooleanField(default=True, required=False)

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

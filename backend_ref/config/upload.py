
from rest_framework import serializers


class UploadImagemSerializer(serializers.Serializer):
    arquivo = serializers.ImageField()

    def validate_arquivo(self, arquivo):
        if arquivo.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "A imagem deve ter no máximo 5 MB."
            )

        if arquivo.content_type not in (
            "image/jpeg",
            "image/png",
            "image/webp",
        ):
            raise serializers.ValidationError(
                "Envie JPG, PNG ou WEBP."
            )

        return arquivo

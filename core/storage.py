"""Backend de armazenamento opcional no Firebase Storage.

Fica desligado por padrão (o projeto usa o disco local em ``media/``). Para
ativar, defina ``USE_FIREBASE_STORAGE=True`` e ``FIREBASE_STORAGE_BUCKET`` no
ambiente — assim os uploads passam a ficar no bucket do Firebase, o que é
necessário em produção (disco local não é durável).
"""

import mimetypes
from datetime import timedelta

from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class FirebaseStorage(Storage):
    """Armazena arquivos no bucket do Firebase Storage do projeto."""

    def __init__(self, bucket_name=None, **kwargs):
        self.bucket_name = bucket_name
        self._bucket = None

    @property
    def bucket(self):
        if self._bucket is None:
            from firebase_admin import storage as firebase_storage

            self._bucket = firebase_storage.bucket(self.bucket_name or None)

        return self._bucket

    def _blob(self, name):
        return self.bucket.blob(name)

    # -- Leitura ------------------------------------------------------------
    def _open(self, name, mode='rb'):
        blob = self._blob(name)

        if not blob.exists():
            raise FileNotFoundError(name)

        return File(blob.download_as_bytes(), name=name)

    def exists(self, name):
        return self._blob(name).exists()

    def size(self, name):
        return self._blob(name).size

    # -- Escrita ------------------------------------------------------------
    def _save(self, name, content):
        blob = self._blob(name)
        content.seek(0)
        tipo = (
            getattr(content, 'content_type', None)
            or mimetypes.guess_type(name)[0]
            or 'application/octet-stream'
        )
        blob.upload_from_file(content, content_type=tipo)
        return name

    def delete(self, name):
        blob = self._blob(name)

        if blob.exists():
            blob.delete()

    def url(self, name):
        blob = self._blob(name)

        try:
            return blob.generate_signed_url(
                version='v4', expiration=timedelta(days=7)
            )
        except Exception:
            # Sem permissão para assinar a URL, tenta a URL pública do objeto.
            return blob.public_url

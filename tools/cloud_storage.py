"""
Abstracción de almacenamiento: usa Google Cloud Storage en producción,
archivos locales en desarrollo. Detecta automáticamente el entorno.
"""

import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
_GCS_BUCKET = os.environ.get("GCS_BUCKET", "")


def _bucket():
    from google.cloud import storage
    return storage.Client().bucket(_GCS_BUCKET)


def leer_json(nombre: str, default):
    """Lee un JSON. En producción desde GCS, en local desde data/."""
    if _GCS_BUCKET:
        try:
            blob = _bucket().blob(nombre)
            if blob.exists():
                return json.loads(blob.download_as_text())
        except Exception as e:
            print(f"[storage] Error leyendo {nombre} de GCS: {e}")
        return default
    else:
        path = DATA_DIR / nombre
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                pass
        return default


def escribir_json(nombre: str, data):
    """Escribe un JSON. En producción a GCS, en local a data/."""
    content = json.dumps(data, ensure_ascii=False, indent=2)
    if _GCS_BUCKET:
        try:
            _bucket().blob(nombre).upload_from_string(
                content, content_type="application/json"
            )
        except Exception as e:
            print(f"[storage] Error escribiendo {nombre} a GCS: {e}")
    else:
        path = DATA_DIR / nombre
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def leer_bytes(nombre: str) -> bytes | None:
    """Lee un archivo binario."""
    if _GCS_BUCKET:
        try:
            blob = _bucket().blob(nombre)
            if blob.exists():
                return blob.download_as_bytes()
        except Exception:
            pass
        return None
    else:
        path = DATA_DIR / nombre
        return path.read_bytes() if path.exists() else None


def escribir_bytes(nombre: str, data: bytes):
    """Escribe un archivo binario."""
    if _GCS_BUCKET:
        try:
            _bucket().blob(nombre).upload_from_string(data)
        except Exception as e:
            print(f"[storage] Error escribiendo bytes {nombre}: {e}")
    else:
        path = DATA_DIR / nombre
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def listar(prefijo: str) -> list[str]:
    """Lista archivos con un prefijo dado."""
    if _GCS_BUCKET:
        try:
            return [b.name for b in _bucket().list_blobs(prefix=prefijo)]
        except Exception:
            return []
    else:
        base = DATA_DIR / prefijo
        if base.is_dir():
            return [str(f.relative_to(DATA_DIR)) for f in base.iterdir()]
        return []


def eliminar(nombre: str):
    """Elimina un archivo."""
    if _GCS_BUCKET:
        try:
            _bucket().blob(nombre).delete()
        except Exception:
            pass
    else:
        path = DATA_DIR / nombre
        if path.exists():
            path.unlink()

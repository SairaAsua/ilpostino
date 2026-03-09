def classify_update(text: str) -> dict:
    """Clasifica el tipo de actualización que viene de Telegram.

    Args:
        text: Mensaje de texto enviado por el usuario via Telegram.

    Returns:
        dict con update_type y confidence.
    """
    text_lower = text.lower()
    if any(w in text_lower for w in ["proyecto", "project", "lancé", "lanzé", "terminé"]):
        return {"update_type": "project_update", "confidence": "high"}
    if any(w in text_lower for w in ["escribí", "blog", "artículo", "post", "publiqué"]):
        return {"update_type": "blog_post", "confidence": "high"}
    if any(w in text_lower for w in ["soy", "me dedico", "trabajo en", "sobre mí"]):
        return {"update_type": "bio_update", "confidence": "medium"}
    return {"update_type": "news", "confidence": "medium"}

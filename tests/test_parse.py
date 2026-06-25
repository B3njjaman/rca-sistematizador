from rca.parse import construir_chunks


def test_chunks_detectan_seccion_y_pagina():
    pages = [
        {"pagina": 1, "texto": "VISTOS:\n\nLo dispuesto en la ley."},
        {"pagina": 2, "texto": "CONSIDERANDO:\n\n9. Que el titular deberá monitorear la flora cada semestre."},
    ]
    chunks = construir_chunks(pages, max_chars=4000)
    assert len(chunks) >= 2
    texto_todo = " ".join(c.fuente for c in chunks)
    assert "Considerando" in texto_todo
    # la fuente incluye la página
    assert any("pág." in c.fuente for c in chunks)


def test_chunk_respeta_max_chars():
    largo = "Párrafo de prueba. " * 100
    pages = [{"pagina": 1, "texto": "\n\n".join([largo] * 6)}]
    chunks = construir_chunks(pages, max_chars=1000)
    assert len(chunks) > 1

from rca.schema import COLUMNAS, Exigencia


def test_columnas_son_31():
    assert len(COLUMNAS) == 31


def test_to_row_cubre_todas_las_columnas():
    ex = Exigencia(nombre="Prueba", transcripcion_literal="texto", tipo="Otro")
    fila = ex.to_row()
    for col in COLUMNAS:
        assert col in fila


def test_estado_por_defecto():
    ex = Exigencia()
    assert ex.estado_cumplimiento == "No iniciado"
    assert ex.riesgo_inherente == "No determinado"

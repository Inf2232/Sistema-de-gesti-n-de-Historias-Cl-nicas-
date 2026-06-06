"""
Controlador del módulo de Nefrología.
Contiene la lógica de negocio y la clasificación KDIGO 2012 de albuminuria.

CAMBIOS DE MODELOS REQUERIDOS (ver sección al final del archivo):
  - Nefrologia.microalbuminuria       → Nefrologia.albuminuria_categoria
  - Nefrologia.microalbuminurias (rel)→ Nefrologia.mediciones_albuminuria
  - Microalbuminuria (clase)          → MedicionAlbuminuria
  - MedicionAlbuminuria.categoria     → campo nuevo (String, nullable)
"""

from datetime import datetime
from collections import Counter

from nicegui import ui
from models import Nefrologia, MedicionAlbuminuria   # ← modelo renombrado
from Errores import log_error_and_notify


# ──────────────────────────────────────────────────────────────────────────────
#  CLASIFICACIÓN KDIGO 2012  (única fuente de verdad — nunca editada por el usuario)
# ──────────────────────────────────────────────────────────────────────────────

# Umbrales por unidad: (límite_A1_A2, límite_A2_A3)
_UMBRALES: dict[str, tuple[float, float]] = {
    'mg/g':    (30.0, 300.0),   # ACR — método preferido clínicamente
    'mg/24h':  (30.0, 300.0),   # AER — recolección de 24 horas
    'mg/mmol': (3.0,  30.0),    # ACR alternativo (SI units)
    # mg/dL solo NO es clasificable sin creatinina → no está aquí a propósito
}


def clasificar_albuminuria(valor: float, unidad: str) -> str | None:
    """
    Clasifica una medición individual de albuminuria según KDIGO 2012.

    Parámetros
    ----------
    valor : float   — Valor numérico de la medición.
    unidad : str    — Unidad ('mg/g', 'mg/24h', 'mg/mmol').

    Retorna
    -------
    'A1', 'A2', 'A3'  o  None si la unidad no permite clasificación directa.

    Notas clínicas
    --------------
    A1 < 30  → Normal a levemente aumentada  (ex «normoalbuminuria»)
    A2 30–300 → Moderadamente aumentada       (ex «microalbuminuria»)
    A3 > 300  → Severamente aumentada         (ex «macroalbuminuria»)
    """
    umbrales = _UMBRALES.get(unidad)
    if umbrales is None:
        return None                     # unidad no clasificable (ej. mg/dL solo)

    lim_inf, lim_sup = umbrales
    if valor < lim_inf:
        return 'A1'
    elif valor <= lim_sup:
        return 'A2'
    else:
        return 'A3'


def derivar_categoria_global(mediciones_data: list[dict]) -> str | None:
    """
    Determina la categoría global del examen a partir de las mediciones individuales.

    Estrategia KDIGO: la categoría más grave con al menos 2 ocurrencias.
    Si sólo hay 1 medición, se usa directamente.
    Si hay varias sin consenso de 2, se usa la más grave disponible.

    Parámetros
    ----------
    mediciones_data : list[dict]
        Lista de dicts con clave 'categoria' ('A1'/'A2'/'A3'/None).

    Retorna
    -------
    'A1', 'A2', 'A3'  o  None.
    """
    cats = [d['categoria'] for d in mediciones_data if d.get('categoria')]
    if not cats:
        return None
    if len(cats) == 1:
        return cats[0]

    conteo = Counter(cats)
    orden = ['A3', 'A2', 'A1']         # de más grave a menos grave

    for cat in orden:
        if conteo.get(cat, 0) >= 2:
            return cat

    # Sin consenso de ≥2: usar la más grave presente
    return min(cats, key=lambda c: orden.index(c))


# ──────────────────────────────────────────────────────────────────────────────
#  HELPERS INTERNOS
# ──────────────────────────────────────────────────────────────────────────────

def _build_valor_uts(selecciones: list | str, otros_input: str) -> str:
    """Construye el string de ultrasonido renal a partir de las selecciones."""
    if not isinstance(selecciones, list):
        return str(selecciones) if selecciones else ""

    filtradas = [s for s in selecciones if s and s.strip()]

    if "Otros" in filtradas:
        filtradas = [s for s in filtradas if s != "Otros"]
        if otros_input and otros_input.strip():
            filtradas.append(f"Otros: {otros_input.strip()}")

    return "; ".join(filtradas)


# ──────────────────────────────────────────────────────────────────────────────
#  MIXIN CONTROLADOR
# ──────────────────────────────────────────────────────────────────────────────

class HistoriaClinicaNefrologiaControllerMixin:
    """
    Mixin con la lógica de negocio del módulo de Nefrología.
    Se combina con HistoriaClinicaNefrologiaViewMixin en el mixin principal.
    """

    # ── GUARDAR (nuevo examen) ────────────────────────────────────────────────

    def guardar_examen_nefrologico(
        self,
        fecha_registro: str,
        filtrado_glomerular_teorico: float,
        creatinina: float,
        urea: float,
        ac_urico: float,
        cituria: str,
        mediciones_data: list[dict],          # ← reemplaza microalbuminuria_data
        proteinuria_valor: float,
        proteinuria_clasificacion: str,
        diagnostico_renal: str,
        uts_renal: list,
        otros_input: str,
        dialog,
    ):
        if not fecha_registro:
            ui.notify('Debe introducir la fecha', type='negative')
            return

        fecha = datetime.strptime(fecha_registro, '%Y-%m-%d').date()
        valor_ultrasonido = _build_valor_uts(uts_renal, otros_input)

        # Categoría global derivada automáticamente — nunca ingresada a mano
        categoria_global = derivar_categoria_global(mediciones_data)

        nuevo_examen = Nefrologia(
            paciente_id=self.paciente.id,
            fecha_registro=fecha,
            filtrado_glomerular_teorico=filtrado_glomerular_teorico,
            creatinina=creatinina,
            urea=urea,
            ac_urico=ac_urico,
            cituria=cituria,
            albuminuria_categoria=categoria_global,   # ← campo renombrado
            proteinuria_valor=proteinuria_valor,
            proteinuria=proteinuria_clasificacion,
            diagnostico_renal=diagnostico_renal,
            uts_renal=valor_ultrasonido,
        )

        for item in mediciones_data:
            ma = MedicionAlbuminuria(
                valor=item['valor'],
                unidad=item['unidad'],
                categoria=item.get('categoria'),      # ← campo nuevo en el modelo
            )
            nuevo_examen.mediciones_albuminuria.append(ma)   # ← relación renombrada

        self.session.add(nuevo_examen)
        self.session.commit()
        ui.notify('Examen nefrológico agregado correctamente', type='positive')
        dialog.close()
        self.mostrar_nefrologia.refresh()

    # ── ACTUALIZAR (examen existente) ─────────────────────────────────────────

    def actualizar_examen_nefrologico(
        self,
        examen,
        fecha_registro: str,
        filtrado_glomerular_teorico: float,
        creatinina: float,
        urea: float,
        ac_urico: float,
        cituria: str,
        mediciones_data: list[dict],
        proteinuria_valor: float,
        proteinuria_clasificacion: str,
        diagnostico_renal: str,
        uts_renal: list,
        otros_input: str,
        dialog,
    ):
        if not fecha_registro:
            ui.notify('Debe introducir la fecha', type='negative')
            return

        valor_ultrasonido = _build_valor_uts(uts_renal, otros_input)
        categoria_global = derivar_categoria_global(mediciones_data)

        # Actualizar campos simples
        examen.fecha_registro = datetime.strptime(fecha_registro, '%Y-%m-%d').date()
        examen.filtrado_glomerular_teorico = filtrado_glomerular_teorico
        examen.creatinina = creatinina
        examen.urea = urea
        examen.ac_urico = ac_urico
        examen.cituria = cituria
        examen.albuminuria_categoria = categoria_global   # ← campo renombrado
        examen.proteinuria_valor = proteinuria_valor
        examen.proteinuria = proteinuria_clasificacion
        examen.diagnostico_renal = diagnostico_renal
        examen.uts_renal = valor_ultrasonido

        # a) Eliminar mediciones que ya no están en la lista temporal
        ids_a_mantener = {item['id'] for item in mediciones_data if 'id' in item}
        examen.mediciones_albuminuria = [
            ma for ma in examen.mediciones_albuminuria if ma.id in ids_a_mantener
        ]

        # b) Agregar las mediciones nuevas (las que no tienen 'id' aún)
        for item in mediciones_data:
            if 'id' not in item:
                ma = MedicionAlbuminuria(
                    valor=item['valor'],
                    unidad=item['unidad'],
                    categoria=item.get('categoria'),
                )
                examen.mediciones_albuminuria.append(ma)

        self.session.commit()
        ui.notify('Examen nefrológico actualizado correctamente', type='positive')
        dialog.close()
        self.mostrar_nefrologia.refresh()

    # ── ELIMINAR ─────────────────────────────────────────────────────────────

    async def _confirmar_eliminacion_nefrologico(self, examen, dialog):
        try:
            self.session.delete(examen)
            self.session.commit()
            ui.notify('Examen nefrológico eliminado correctamente', type='positive')
            self.mostrar_nefrologia.refresh()
        except Exception as e:
            log_error_and_notify(e, f'Error al eliminar el examen nefrológico: {str(e)}')
        finally:
            dialog.close()


# ──────────────────────────────────────────────────────────────────────────────
#  CAMBIOS REQUERIDOS EN LOS MODELOS  (models.py)
# ──────────────────────────────────────────────────────────────────────────────
#
#  1. Clase Nefrologia:
#     ANTES:  microalbuminuria = Column(String)           # "Normal" / "Patologica"
#     AHORA:  albuminuria_categoria = Column(String)      # "A1" / "A2" / "A3" / None
#
#     ANTES:  microalbuminurias = relationship("Microalbuminuria", ...)
#     AHORA:  mediciones_albuminuria = relationship("MedicionAlbuminuria", ...)
#
#  2. Renombrar clase Microalbuminuria → MedicionAlbuminuria:
#     ANTES:
#       class Microalbuminuria(Base):
#           id        = Column(Integer, primary_key=True)
#           examen_id = Column(Integer, ForeignKey("nefrologia.id"))
#           valor     = Column(Float)
#           unidad    = Column(String)
#
#     AHORA:
#       class MedicionAlbuminuria(Base):
#           __tablename__ = "medicion_albuminuria"  # nueva tabla o renombrada
#           id        = Column(Integer, primary_key=True)
#           examen_id = Column(Integer, ForeignKey("nefrologia.id"))
#           valor     = Column(Float, nullable=False)
#           unidad    = Column(String, nullable=False)     # 'mg/g' | 'mg/24h' | 'mg/mmol'
#           categoria = Column(String, nullable=True)      # 'A1' | 'A2' | 'A3' ← CAMPO NUEVO
#
#  3. Migración de datos sugerida (Alembic o script manual):
#     - Nefrologia.microalbuminuria == "Normal"    → albuminuria_categoria = "A1"
#     - Nefrologia.microalbuminuria == "Patologica"→ albuminuria_categoria = NULL
#       (dejar en NULL y recalcular desde los valores, que es lo correcto)
#     - Microalbuminuria.unidad == "mg/dL": marcar como no clasificable
#       (sugerido: cambiar a NULL o agregar nota; mg/dL solo no clasifica KDIGO)
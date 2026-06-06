# audit_controller.py
from models import Session, LogAuditoria
from datetime import datetime, timedelta

class AuditController:
    def obtener_logs_filtrados(self, usuario, accion, dias_periodo):
        """
        Consulta los registros de auditoría aplicando filtros de forma óptima
        y garantizando el cierre inmediato de la conexión.
        """
        db = Session()
        try:
            query = db.query(LogAuditoria)

            # 1. Filtro por Periodo de Tiempo
            if dias_periodo and dias_periodo != 0:
                desde = datetime.utcnow() - timedelta(days=int(dias_periodo))
                query = query.filter(LogAuditoria.fecha >= desde)

            # 2. Filtro por Usuario
            if usuario:
                query = query.filter(LogAuditoria.usuario.ilike(f'%{usuario}%'))

            # 3. Filtro por Acción específica
            if accion:
                query = query.filter(LogAuditoria.accion == accion)

            # Limitamos a los últimos 200 registros por optimización de rendimiento en la UI
            logs = query.order_by(LogAuditoria.fecha.desc()).limit(200).all()

            # Mapeo a estructuras nativas de Python (Desacoplando los modelos SQLAlchemy de la Vista)
            rows = []
            for log in logs:
                rows.append({
                    'id_interno': f"{log.fecha.timestamp()}_{log.usuario}_{log.registro_id or 'na'}",
                    'fecha': log.fecha.strftime('%Y-%m-%d %H:%M:%S'),
                    'usuario': log.usuario,
                    'accion': log.accion,
                    'tabla': log.tabla,
                    'registro_id': log.registro_id or 'N/A',
                    'raw_detalles': log.detalles  # Mantenemos el JSON para cuando sea solicitado
                })
            return rows
        finally:
            db.close()
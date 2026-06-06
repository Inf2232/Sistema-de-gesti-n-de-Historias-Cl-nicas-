import os
import shutil
import sqlite3
from datetime import datetime
import traceback

class DatabaseController:
    def __init__(self):
        # 1. CORRECCIÓN DE RUTAS: Subimos un nivel desde 'controllers' hacia la raíz de 'app'
        # Ajusta esto dependiendo de tu estructura real. Esto asume: app/controllers/database_controller.py
        base_dir = os.path.dirname(os.path.dirname(__file__)) 
        
        self.db_path = os.path.join(base_dir, 'data', 'diabetes_app.db')
        self.backup_dir = os.path.join(base_dir, 'backups_automaticos')

    def obtener_ruta_base_datos(self):
        """Retorna la ubicación física de la DB activa para su descarga."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError("El archivo de la base de datos activa no existe.")
        return self.db_path

    def restaurar_desde_bytes(self, file_bytes):
        """Procesa el flujo binario del archivo subido y clona."""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)

            # 1. Respaldo preventivo
            if os.path.exists(self.db_path):
                pre_restore_path = os.path.join(
                    self.backup_dir,
                    f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                )
                shutil.copy2(self.db_path, pre_restore_path)

            # 2. Persistir temporalmente
            temp_path = os.path.join(self.backup_dir, "temp_upload.db")
            with open(temp_path, "wb") as f:
                f.write(file_bytes)

            # 3. Sincronización
            self._sincronizar_tablas(origen=temp_path, destino=self.db_path)

            # 4. Limpieza
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return True, "Base de datos restaurada con éxito."

        except Exception as e:
            print("\n" + "=" * 60)
            print("[DEBUG] DETECTADO FALLO CRÍTICO:")
            traceback.print_exc()
            print("=" * 60 + "\n")

            if "temp_path" in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

            return False, f"Fallo en la restauración: {str(e)}"

    def _sincronizar_tablas(self, origen, destino):
        """Método privado que realiza la clonación atómica mediante SQLite,

        soportando cambios de esquemas, columnas faltantes, nuevas o nulas entre versiones.
        """
        if not os.path.exists(destino):
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copy2(origen, destino)
            return

        conn_destino = sqlite3.connect(destino)
        try:
            origen_seguro = origen.replace('\\', '/')
            conn_destino.execute(f"ATTACH '{origen_seguro}' AS backup_db;")
            cursor_destino = conn_destino.cursor()

            # Obtener las tablas que espera el sistema actual (destino)
            cursor_destino.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tablas = [t[0] for t in cursor_destino.fetchall() if t[0] != 'sqlite_sequence']

            if not tablas:
                raise ValueError("La base de datos actual de destino no tiene tablas cargadas.")

            for tabla in tablas:
                # 1. VALIDACIÓN: ¿La tabla existe en la base de datos vieja?
                # Si es una tabla nueva de sprints recientes, no existirá en el respaldo.
                cursor_destino.execute(
                    "SELECT name FROM backup_db.sqlite_master WHERE type='table' AND name=?;", 
                    (tabla,)
                )
                if not cursor_destino.fetchone():
                    print(f"[DEBUG MIGRACIÓN] La tabla '{tabla}' no existe en el respaldo viejo. Se omite de forma segura.")
                    continue

                # 2. INSPECCIÓN DE ESQUEMAS
                # Obtener info del destino (Esquema nuevo): (cid, name, type, notnull, dflt_value, pk)
                cursor_destino.execute(f"PRAGMA table_info({tabla});")
                dest_cols_info = cursor_destino.fetchall()
                
                # Obtener nombres de columnas del origen (Esquema viejo)
                cursor_destino.execute(f"PRAGMA backup_db.table_info({tabla});")
                src_col_names = [col[1] for col in cursor_destino.fetchall()]

                # Limpiar la tabla destino antes de la migración
                cursor_destino.execute(f"DELETE FROM {tabla};")

                dest_col_names = []
                select_expressions = []

                # 3. MAPEO INTELIGENTE COLUMNA POR COLUMNA
                for col in dest_cols_info:
                    c_name = col[1]
                    c_notnull = col[3]
                    c_type = col[2].upper()

                    dest_col_names.append(f'"{c_name}"')

                    # Establecer un valor de rescate (fallback) coherente si el campo exige NOT NULL
                    if 'INT' in c_type or 'BOOL' in c_type:
                        # Si falta institucion_id o activo, asumimos 1 (institución base / activo por defecto)
                        fallback = "1" if c_name in ['institucion_id', 'activo'] else "0"
                    elif 'FLOAT' in c_type or 'REAL' in c_type:
                        fallback = "0.0"
                    else:
                        fallback = "''"  # Cadenas vacías para VARCHAR/TEXT/JSON

                    if c_name in src_col_names:
                        # Caso A: La columna existe en la base de datos vieja.
                        # Si ahora es NOT NULL, usamos COALESCE para salvaguardar registros antiguos con NULLs indeseados.
                        if c_notnull:
                            select_expressions.append(f'COALESCE(backup_db.{tabla}."{c_name}", {fallback})')
                        else:
                            select_expressions.append(f'backup_db.{tabla}."{c_name}"')
                    else:
                        # Caso B: Es una columna nueva que añadiste en los últimos modelos.
                        # Al no existir en la DB vieja, inyectamos el fallback o un NULL controlado.
                        if c_notnull:
                            select_expressions.append(f'{fallback} AS "{c_name}"')
                        else:
                            select_expressions.append(f'NULL AS "{c_name}"')

                # 4. EJECUCIÓN DEL MIGRADOR DINÁMICO
                str_dest_cols = ", ".join(dest_col_names)
                str_select = ", ".join(select_expressions)

                sql_migracion = f"INSERT INTO {tabla} ({str_dest_cols}) SELECT {str_select} FROM backup_db.{tabla};"
                cursor_destino.execute(sql_migracion)

            conn_destino.commit()
            print("[MIGRADOR] Restauración y reajuste de esquemas completado con éxito.")
        except Exception as e:
            conn_destino.rollback()
            raise e
        finally:
            conn_destino.close()
# Sistema-de-gesti-n-de-Historias-Cl-nicas-
Aplicación web desarrollada con NiceGui para gestionar las historias clínicas en la Clínica del Diabético Perteneciente al Hospital provincial de Cienfuegos ,Gustavo Aldereguía Lima

# HCE Médica — Sistema de Historia Clínica Electrónica

Sistema de escritorio para la gestión integral de historias clínicas en instituciones de salud. Desarrollado como tesis de grado en la Universidad de Cienfuegos Carlos Rafael Rodríguez, Cuba (2026).

Presentado como póster científico en el **XI Congreso Cubano de Diabetes — CUBADIAB 2025** (La Habana, noviembre 2025), avalado por la Organización Panamericana de la Salud (OPS), obteniendo **Premio** — máxima distinción del evento.

---

## Tecnologías

- **Python 3.13** — lenguaje principal
- **NiceGUI** — interfaz de usuario de escritorio
- **SQLAlchemy** — ORM y acceso a datos
- **SQLite** — base de datos local
- **Alembic** — migraciones de base de datos
- **Pytest** — pruebas automatizadas
- **Docker** — contenerización

---

## Funcionalidades

- Gestión completa de historias clínicas electrónicas
- Autenticación y control de acceso por roles (médico, enfermero, administrador)
- Módulo especializado para pacientes con diabetes mellitus y nefrología (clasificación KDIGO)
- Indicadores clínicos según estándares OMS
- Exportación de informes clínicos en PDF
- Backups automáticos de la base de datos

---

## Arquitectura

El sistema aplica una arquitectura en capas con separación clara entre modelos, controladores y vistas, usando los patrones Repository, MVC y control de acceso basado en roles (RBAC).

```
hce-medica/
├── models.py          # Modelos de datos (SQLAlchemy ORM)
├── controllers/       # Lógica de negocio
├── views/             # Interfaces NiceGUI
├── tests/             # Suite de pruebas (caja negra y caja blanca)
├── docs/              # Manual de usuario
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## Instalación

```bash
git clone Inf2232/Sistema-de-gesti-n-de-Historias-Cl-nicas-
cd hce-medica

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
python inicializador.py
python programa.py
```

Con Docker:

```bash
docker-compose up --build
```

---

## Pruebas

```bash
pytest tests/ -v
```

Las pruebas cubren autenticación, validación de registros clínicos, cálculo de indicadores y exportación de datos.

---

---

## Nota de privacidad

Este repositorio no contiene datos reales de pacientes. La base de datos con información clínica está excluida por razones de privacidad.

---

## Autor

**Carlos Alejandro Pescoso Reyes** — Ingeniero Informático  
Universidad de Cienfuegos · Cuba · 2026  
carlospescoso03@gmail.com · [LinkedIn](https://linkedin.com/in/carlos-pescoso-287ba7223) · [GitHub](https://github.com/inf2232)

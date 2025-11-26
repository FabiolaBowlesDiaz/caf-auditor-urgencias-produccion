# Changelog - Sistema de Auditoría de Urgencias

Todas las modificaciones notables a este proyecto serán documentadas en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] - 2025-11-26

### Inicial Release - Adaptado de Sistema de Emergencias

**Sistema de auditoría automática para el Servicio de Urgencias de Clínica Foianini.**

#### Origen
Adaptado desde `CAF_Auditor_Emergencias_Produccion` v1.2.2 con los siguientes cambios específicos para Urgencias:

#### Cambios en Queries SQL

**`queries/get_todas_atenciones_24h.sql`**
- Cambio de Sector: `PacienteEvolucionSector = 3` → `PacienteEvolucionSector = 50` (Urgencias)
- Nuevo filtro: Agregado `INNER JOIN turno t ON pe.TurnoNumero = t.TurnoNumero`
- Nuevo filtro: Agregado `WHERE t.TurnoTipo = 'E'` (solo urgencias, excluye consultas 'P' y sobrecupo 'S')
- Mantiene filtro temporal: últimas 24 horas automático con `DATE_SUB(NOW(), INTERVAL 24 HOUR)`

**`queries/get_detalle_atencion.sql`**
- Copiado idéntico desde sistema de Emergencias
- Incluye fix v1.2.2: campo `PacienteEvolucionEvFinal` en evoluciones

#### Cambios en Scripts Python

**`main.py`**
- Modelo de datos: `AuditoriaEmergenciaResultado` → `AuditoriaUrgenciaResultado`
- Campo diagnóstico: `diagnostico_emergencia` → `diagnostico_urgencia`
- Prompt del sistema: Actualizado para contexto de urgencias
  - Agregado: "Urgencias atiende casos de menor complejidad que emergencias"
  - Agregado: "Los tiempos de respuesta pueden ser ligeramente más flexibles"
- Archivos de salida: `auditoria_emergencias_*.jsonl` → `auditoria_urgencias_*.jsonl`
- Logs: Todos los mensajes actualizados con "URGENCIAS" en lugar de "EMERGENCIAS"

**`auditar_atencion.py`**
- Import: `AuditoriaEmergenciaResultado` → `AuditoriaUrgenciaResultado`
- HTML template: "Servicio de Emergencias" → "Servicio de Urgencias"
- Campo diagnóstico: `diagnostico_emergencia` → `diagnostico_urgencia`

**`generar_reporte.py`**
- HTML title: "Servicio de Emergencias" → "Servicio de Urgencias"
- Análisis de datos: `diagnostico_emergencia` → `diagnostico_urgencia`
- Portada del reporte: "Evaluación de Calidad Asistencial - Servicio de Urgencias"
- Footer: Referencias actualizadas a "Servicio de Urgencias"

**`ver_historial_raw.py`**
- Copiado idéntico (herramienta de diagnóstico genérica, sin cambios necesarios)

#### Archivos de Configuración

**`pyproject.toml`**
- Nombre del proyecto: `auditoria-emergencia` → `auditoria-urgencia`
- Descripción: Actualizada para "medicina de urgencias"
- Versión inicial: 1.0.0
- Dependencias: Idénticas al sistema de Emergencias

**`.env.example`**
- Actualizado con mejores comentarios
- Eliminadas referencias a API PHP (no usada en este sistema)
- Estructura limpia para MySQL + OpenRouter

**`README.md`**
- Documentación completa específica para Urgencias
- Sección destacada explicando diferencias con Emergencias:
  - Sector 50 (vs Sector 3)
  - Filtro adicional TurnoTipo = 'E'
  - Tiempos más flexibles
- Ejemplos de queries SQL con filtros correctos
- Estimaciones de volumen y costos

#### Características Heredadas (v1.2.2 de Emergencias)

✅ **Fix crítico de GROUP_CONCAT**
- Configuración de `group_concat_max_len = 10MB` para capturar evoluciones completas
- Sin este fix, las evoluciones clínicas se truncaban y NO llegaban a Claude

✅ **Prompt mejorado para acto médico**
- Evaluación enfocada en ACTO MÉDICO CLÍNICO
- NO evalúa calidad de documentación
- Ejemplos específicos de qué SÍ y qué NO evaluar

✅ **Campo `PacienteEvolucionEvFinal`**
- Captura de evaluación final (epicrisis)
- Crítico para detección de referencias y planes de alta

✅ **Tracking de estado robusto**
- Seguimiento por evolución de estado (pendiente/completado/fallido)
- Recuperación ante fallos

✅ **Herramienta de diagnóstico**
- `ver_historial_raw.py` para depuración

#### Validación Pendiente

🔲 Validar query retorna solo atenciones de Urgencias (Sector 50 + TurnoTipo E)
🔲 Ejecutar auditoría individual de prueba
🔲 Verificar formato de reportes HTML
🔲 Confirmar campos `diagnostico_urgencia` en JSONL

#### Notas de Compatibilidad

- **Base de datos**: Comparte misma conexión MySQL que sistema de Emergencias (`foianiniprod_mysql`)
- **Guías clínicas**: Usa mismas referencias internacionales (WHO, AHA, NICE, ERC, ACS, ACEP)
- **Modelo de IA**: Claude Sonnet 4.5 (idéntico al sistema de Emergencias)
- **Formato de datos**: Compatible con sistema de Emergencias (solo cambia nombre de campo diagnóstico)

---

## Formato de Versiones

- **[X.Y.Z]** - Versión semántica
  - X: Cambios mayores no retrocompatibles
  - Y: Nuevas funcionalidades retrocompatibles
  - Z: Correcciones de bugs

## Categorías de Cambios

- **Added**: Nuevas funcionalidades
- **Changed**: Cambios en funcionalidad existente
- **Deprecated**: Funcionalidades que serán removidas
- **Removed**: Funcionalidades removidas
- **Fixed**: Correcciones de bugs
- **Security**: Correcciones de seguridad

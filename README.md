# Sistema de Auditoría de Urgencias - Clínica Foianini

Sistema automatizado de auditoría médica para el servicio de **Urgencias** usando inteligencia artificial (Claude Sonnet 4.5).

## Descripción

Este sistema evalúa la calidad de las atenciones médicas en urgencias según guías clínicas internacionales (WHO, AHA, NICE, ERC, ACS, ACEP), generando reportes ejecutivos automáticos.

### Diferencia con Emergency

Este sistema audita atenciones del **Servicio de Urgencias** (casos de menor complejidad):
- **Sector**: 50 (Urgencias)
- **Filtro adicional**: TurnoTipo = 'E' (tipo Urgencia)
- **Guías aplicables**: Mismas que Emergencias (WHO, AHA, NICE, etc.)
- **Tiempos de respuesta**: Ligeramente más flexibles que emergencias críticas

## Características

- Auditoría diaria automática de TODAS las atenciones de urgencias (últimas 24h)
- Auditoría individual por número de cuenta
- Evaluación con IA usando Claude Sonnet 4.5
- Reportes HTML interactivos con filtros por médico
- Score de calidad 0-100 por atención
- Adherencia a guías internacionales

## Instalación

### 1. Requisitos
- Python 3.13+
- MySQL con acceso a base `foianiniprod_mysql`
- Cuenta en OpenRouter con saldo

### 2. Instalar dependencias

```bash
# Con uv (recomendado)
uv pip install .

# O con pip tradicional
pip install -e .
```

### 3. Configurar variables de entorno

Copiar `.env.example` a `.env` y configurar:

```env
# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-tu_api_key_aqui

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=tu_usuario
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=foianiniprod_mysql
```

## Uso

### Auditoría Diaria Completa

Audita TODAS las atenciones de urgencias de las últimas 24 horas:

```bash
python main.py
```

**Salida:**
- `output/auditoria_urgencias_YYYYMMDD_HHMMSS.jsonl` (datos)
- `output/auditoria_urgencias_YYYYMMDD_HHMMSS.html` (reporte interactivo)
- `output/tracking_YYYYMMDD_HHMMSS.json` (estado del proceso)

### Auditoría Individual

Audita una atención específica por número de cuenta:

```bash
# Formato: GESTION/INTERNACION
python auditar_atencion.py 2025/148894

# O con argumentos separados
python auditar_atencion.py --gestion 2025 --internacion 148894

# Modo interactivo
python auditar_atencion.py
```

**Salida:**
- `output/atencion_GESTION_INTERNACION_YYYYMMDD_HHMMSS.json`
- `output/atencion_GESTION_INTERNACION_YYYYMMDD_HHMMSS.html`
- Resumen en consola

## Criterios de Evaluación

El sistema evalúa:
- Diagnóstico oportuno y certero
- Estudios solicitados apropiados al diagnóstico
- Tratamiento administrado correcto según guías
- Tiempo de atención adecuado para urgencias
- Adherencia a guías internacionales

**IMPORTANTE**: Se evalúa el **acto médico clínico**, NO la calidad de documentación.

## Guías Clínicas de Referencia

- **WHO** - World Health Organization
- **AHA** - American Heart Association
- **NICE** - National Institute for Health and Care Excellence
- **ERC** - European Resuscitation Council
- **ACS** - American College of Surgeons
- **ACEP** - American College of Emergency Physicians

## Herramientas de Diagnóstico

### Ver historial enviado a Claude

```bash
python ver_historial_raw.py 2025/148894
```

Genera archivo `historial_raw_2025_148894.txt` con el contenido exacto que se envía al LLM.

## Configuración Avanzada

### Consultas SQL

**Filtros de Urgencias:**
```sql
WHERE pe.PacienteEvolucionSector = 50  -- Sector Urgencias
  AND t.TurnoTipo = 'E'  -- Tipo de turno: Urgencia (no Consulta 'P' ni Sobrecupo 'S')
  AND pe.PacienteEvolucionFechaHora >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
```

## Solución de Problemas

### Error: No se encontraron atenciones

Verificar en MySQL:
```sql
SELECT COUNT(*)
FROM pacienteevolucion pe
INNER JOIN turno t ON pe.TurnoNumero = t.TurnoNumero
WHERE pe.PacienteEvolucionSector = 50
  AND t.TurnoTipo = 'E'
  AND pe.PacienteEvolucionFechaHora >= DATE_SUB(NOW(), INTERVAL 24 HOUR);
```

### Error de conexión MySQL

Verificar credenciales en `.env` y acceso a la base de datos.

### Error de API OpenRouter

Verificar:
- API key válida
- Saldo disponible en cuenta
- Conectividad a internet

## Logs

Los logs se guardan en `logs/auditoria_YYYYMMDD.log` con:
- Timestamp de cada operación
- Detalles de atenciones procesadas
- Errores y advertencias

## Modelo de IA

- **Principal**: Claude Sonnet 4.5 (openrouter/anthropic/claude-sonnet-4.5)
- **Fallback**: Claude Sonnet 4 (openrouter/anthropic/claude-sonnet-4)
- **Temperature**: 0.3 (determinístico)
- **Reintentos**: 3 por modelo (6 total)

## Estimaciones

- **Tiempo por atención**: ~90 segundos
- **Costo por atención**: ~$0.02 USD
- **Volumen esperado**: 40-60 atenciones/día
- **Tiempo total diario**: ~60-90 minutos
- **Costo mensual**: ~$36 USD

## Seguridad

- **NO versionar** el archivo `.env`
- Usar credenciales de **solo lectura** para MySQL
- Restringir acceso a reportes (contienen datos sensibles)
- Logs y outputs en `.gitignore`

## Soporte

Para reportar problemas o sugerir mejoras, contactar al equipo de sistemas.

---

**Versión**: 1.0.0
**Última actualización**: Noviembre 2025
**Basado en**: CAF_Auditor_Emergencias_Produccion v1.2.2

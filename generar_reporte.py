import json
import os
from collections import Counter
from datetime import datetime

# Cargar datos
def cargar_datos(archivo):
    """Carga datos desde archivo JSONL"""
    if not os.path.exists(archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {archivo}")

    with open(archivo, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

# Análisis de datos mejorado
def analizar_datos(data):
    """Analiza los datos de auditorías de urgencia con mayor detalle"""
    if not data:
        raise ValueError("No hay datos para analizar")

    total = len(data)
    score_promedio = sum(d['score_calidad'] for d in data) / total
    cumplen = sum(1 for d in data if d['cumple_guias'].lower() in ['sí', 'si', 'yes'])

    # Por médico
    medicos = {}
    for d in data:
        medico_id = d['id_medico']
        if medico_id not in medicos:
            medicos[medico_id] = {
                'nombre': d['nombre_medico'],
                'atenciones': [],
                'scores': [],
                'cumplimientos': [],
                'diagnosticos': [],
                'guias_usadas': [],
                'hallazgos_criticos_total': [],
                'recomendaciones_total': []
            }

        medicos[medico_id]['atenciones'].append(d)
        medicos[medico_id]['scores'].append(d['score_calidad'])
        medicos[medico_id]['cumplimientos'].append(d['cumple_guias'])
        medicos[medico_id]['diagnosticos'].append(d['diagnostico_urgencia'])
        medicos[medico_id]['guias_usadas'].extend(d['guias_aplicables'])
        medicos[medico_id]['hallazgos_criticos_total'].extend(d['hallazgos_criticos'])
        medicos[medico_id]['recomendaciones_total'].extend(d['recomendaciones'])

    # Guías clínicas utilizadas
    todas_guias = []
    for d in data:
        todas_guias.extend(d['guias_aplicables'])

    # Contadores de guías por organización
    guias_counter = Counter(todas_guias)
    guias_por_org = {
        'WHO': sum(v for k, v in guias_counter.items() if 'WHO' in k.upper()),
        'AHA': sum(v for k, v in guias_counter.items() if 'AHA' in k.upper()),
        'NICE': sum(v for k, v in guias_counter.items() if 'NICE' in k.upper()),
        'ERC': sum(v for k, v in guias_counter.items() if 'ERC' in k.upper()),
        'ACEP': sum(v for k, v in guias_counter.items() if 'ACEP' in k.upper()),
        'ASCRS': sum(v for k, v in guias_counter.items() if 'ASCRS' in k.upper()),
        'ACS': sum(v for k, v in guias_counter.items() if 'ACS' in k.upper()),
        'Otras': sum(v for k, v in guias_counter.items()
                    if not any(org in k.upper() for org in ['WHO', 'AHA', 'NICE', 'ERC', 'ACEP', 'ASCRS', 'ACS']))
    }

    # Tratamientos y hallazgos
    todos_hallazgos = []
    todas_recomendaciones = []
    for d in data:
        todos_hallazgos.extend(d['hallazgos_criticos'])
        todas_recomendaciones.extend(d['recomendaciones'])

    # Distribución de scores
    distribucion_scores = {
        'excelente': sum(1 for d in data if d['score_calidad'] >= 80),
        'bueno': sum(1 for d in data if 60 <= d['score_calidad'] < 80),
        'regular': sum(1 for d in data if 40 <= d['score_calidad'] < 60),
        'deficiente': sum(1 for d in data if d['score_calidad'] < 40)
    }

    return {
        'total': total,
        'score_promedio': score_promedio,
        'cumplen': cumplen,
        'medicos': medicos,
        'guias': guias_counter,
        'guias_por_org': guias_por_org,
        'hallazgos': Counter(todos_hallazgos),
        'recomendaciones': Counter(todas_recomendaciones),
        'score_max': max(d['score_calidad'] for d in data),
        'score_min': min(d['score_calidad'] for d in data),
        'pacientes_unicos': len(set(d['id_persona_paciente'] for d in data)),
        'distribucion_scores': distribucion_scores
    }

# Helper para generar botones de filtro
def generar_botones_filtro(analisis):
    """Genera HTML de botones de filtrado por médico"""
    total = analisis['total']
    medicos = analisis['medicos']

    html = f'            <button class="btn-filtro active" data-medico-id="todos" onclick="filtrarPorMedico(\'todos\')">📊 TODOS ({total})</button>\n'

    # Ordenar médicos por nombre
    medicos_ordenados = sorted(medicos.items(), key=lambda x: x[1]['nombre'])

    for medico_id, info in medicos_ordenados:
        nombre = info['nombre']
        count = len(info['atenciones'])
        html += f'            <button class="btn-filtro" data-medico-id="{medico_id}" onclick="filtrarPorMedico(\'{medico_id}\')">👨‍⚕️ {nombre} ({count})</button>\n'

    return html

# Generar HTML mejorado
def generar_html(data, analisis, archivo_salida):
    """Genera el reporte HTML de auditoría de emergencia - Versión Ejecutiva"""

    fecha_reporte = datetime.now().strftime("%d de %B de %Y")

    # Calcular rango de fechas del periodo analizado
    fechas = [datetime.strptime(d['fecha_atencion'], '%Y-%m-%d %H:%M:%S') for d in data]
    fecha_min = min(fechas)
    fecha_max = max(fechas)

    # Traducir mes al español
    meses = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo',
        'April': 'abril', 'May': 'mayo', 'June': 'junio',
        'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
        'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    fecha_min_str = fecha_min.strftime('%d de %B %Y %H:%M')
    fecha_max_str = fecha_max.strftime('%d de %B %Y %H:%M')
    for en, es in meses.items():
        fecha_min_str = fecha_min_str.replace(en, es)
        fecha_max_str = fecha_max_str.replace(en, es)

    periodo_texto = f"Del {fecha_min_str} al {fecha_max_str}"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auditoría Médica - Servicio de Urgencias | Clínica Foianini</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background: #f1f5f9;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Portada - Azul (mucho más compacta) */
        .portada {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 20px 25px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 8px 20px rgba(30, 64, 175, 0.3);
            margin-bottom: 15px;
        }}

        .portada h1 {{
            font-size: 1.4em;
            margin-bottom: 6px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}

        .portada .subtitulo {{
            font-size: 0.85em;
            opacity: 0.95;
            margin-bottom: 8px;
        }}

        .portada .fecha {{
            font-size: 0.8em;
            opacity: 0.9;
            margin-top: 8px;
            padding: 5px 12px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            display: inline-block;
        }}

        /* Tarjetas de resumen (mucho más compactas) */
        .resumen-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }}

        .tarjeta-resumen {{
            background: white;
            padding: 12px 15px;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(30, 64, 175, 0.08);
            border-left: 3px solid #3b82f6;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .tarjeta-resumen:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30, 64, 175, 0.12);
        }}

        .tarjeta-resumen .icono {{
            font-size: 1.3em;
            margin-bottom: 5px;
            color: #3b82f6;
        }}

        .tarjeta-resumen .valor {{
            font-size: 1.4em;
            font-weight: 700;
            color: #1e40af;
            margin: 5px 0;
        }}

        .tarjeta-resumen .etiqueta {{
            color: #64748b;
            font-size: 0.7em;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            font-weight: 600;
        }}

        .tarjeta-resumen .detalle {{
            color: #475569;
            font-size: 0.7em;
            margin-top: 5px;
            padding-top: 5px;
            border-top: 1px solid #e2e8f0;
        }}

        /* Secciones (más compactas) */
        .seccion {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 6px rgba(30, 64, 175, 0.08);
        }}

        .seccion h2 {{
            color: #1e40af;
            font-size: 1.5em;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 2px solid #3b82f6;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .seccion h3 {{
            color: #1e40af;
            font-size: 1.2em;
            margin: 20px 0 12px 0;
            padding-left: 10px;
            border-left: 3px solid #60a5fa;
        }}

        /* Tablas más compactas */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            font-size: 0.9em;
        }}

        /* Contenedor de tabla con scroll horizontal */
        .tabla-scroll {{
            overflow-x: auto;
            margin: 15px 0;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(30, 64, 175, 0.08);
        }}

        .tabla-scroll table {{
            min-width: 1000px;
            margin: 0;
        }}

        thead {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
        }}

        th {{
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}

        tbody tr {{
            transition: background-color 0.2s;
        }}

        tbody tr:hover {{
            background-color: #f8fafc;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        /* Badges de score */
        .score-badge {{
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            display: inline-block;
        }}

        .score-excelente {{
            background: #dcfce7;
            color: #166534;
        }}

        .score-bueno {{
            background: #dbeafe;
            color: #1e40af;
        }}

        .score-regular {{
            background: #fef3c7;
            color: #92400e;
        }}

        .score-deficiente {{
            background: #fee2e2;
            color: #991b1b;
        }}

        /* Listas */
        ul, ol {{
            margin: 15px 0 15px 25px;
            line-height: 1.8;
        }}

        li {{
            margin: 8px 0;
            color: #475569;
        }}

        li strong {{
            color: #1e40af;
        }}

        /* Cajas de información */
        .info-box {{
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid;
        }}

        .info-box.critico {{
            background: #fee2e2;
            border-color: #dc2626;
            color: #7f1d1d;
        }}

        .info-box.advertencia {{
            background: #fef3c7;
            border-color: #f59e0b;
            color: #78350f;
        }}

        .info-box.info {{
            background: #dbeafe;
            border-color: #3b82f6;
            color: #1e40af;
        }}

        .info-box.exito {{
            background: #dcfce7;
            border-color: #10b981;
            color: #065f46;
        }}

        /* Detalles de atenciones */
        .atencion-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            transition: all 0.2s;
        }}

        .atencion-card:hover {{
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
        }}

        .atencion-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e2e8f0;
        }}

        .atencion-meta {{
            font-size: 0.9em;
            color: #64748b;
            margin: 8px 0;
        }}

        .criterios-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 15px 0;
        }}

        .criterios-columna {{
            padding: 15px;
            border-radius: 6px;
        }}

        .criterios-cumplidos {{
            background: #f0fdf4;
            border: 1px solid #86efac;
        }}

        .criterios-no-cumplidos {{
            background: #fef2f2;
            border: 1px solid #fca5a5;
        }}

        .criterios-columna h4 {{
            margin-bottom: 12px;
            font-size: 1em;
        }}

        .criterios-cumplidos h4 {{
            color: #166534;
        }}

        .criterios-no-cumplidos h4 {{
            color: #991b1b;
        }}

        .criterios-columna ul {{
            margin-left: 20px;
        }}

        .criterios-columna li {{
            margin: 6px 0;
            font-size: 0.9em;
        }}

        /* Gráfico de distribución */
        .chart-container {{
            margin: 25px 0;
            padding: 20px;
            background: #f8fafc;
            border-radius: 8px;
        }}

        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .bar-row {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .bar-label {{
            min-width: 120px;
            font-weight: 600;
            color: #475569;
            font-size: 0.9em;
        }}

        .bar {{
            flex: 1;
            height: 32px;
            background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
            border-radius: 6px;
            position: relative;
            transition: all 0.3s;
        }}

        .bar:hover {{
            transform: scaleX(1.02);
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }}

        .bar-value {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: white;
            font-weight: 600;
            font-size: 0.9em;
        }}

        /* Impresión */
        @media print {{
            .container {{
                max-width: 100%;
            }}

            .seccion {{
                page-break-inside: avoid;
            }}

            .portada {{
                page-break-after: always;
            }}
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            font-size: 0.9em;
            margin-top: 40px;
        }}

        .footer-divider {{
            width: 100px;
            height: 3px;
            background: linear-gradient(90deg, transparent, #3b82f6, transparent);
            margin: 20px auto;
        }}

        /* Número grande para score */
        .score-grande {{
            font-size: 4em;
            font-weight: 700;
            color: #1e40af;
            line-height: 1;
        }}

        /* Progreso visual */
        .progress-bar {{
            width: 100%;
            height: 12px;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
            border-radius: 10px;
            transition: width 0.5s ease;
        }}

        /* Estilo del periodo en portada */
        .portada .periodo {{
            font-size: 0.75em;
            opacity: 0.9;
            margin-top: 8px;
            padding: 5px 12px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            display: inline-block;
            font-style: italic;
        }}

        /* Contenedor de filtros con estilo similar al ejemplo */
        .filtros-medicos {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 20px;
            padding: 15px 20px;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}

        /* Botones de filtro */
        .btn-filtro {{
            padding: 10px 18px;
            border: none;
            background: transparent;
            color: #64748b;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            border-radius: 6px 6px 0 0;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
            white-space: nowrap;
        }}

        .btn-filtro:hover {{
            background: #f1f5f9;
            color: #1e40af;
        }}

        .btn-filtro.active {{
            background: #dbeafe;
            color: #1e40af;
            border-bottom-color: #3b82f6;
        }}
    </style>
</head>
<body>
    <div class="container">
"""

    # PORTADA
    html += f"""
        <!-- PORTADA -->
        <div class="portada">
            <h1>📊 Auditoría Médica</h1>
            <div class="subtitulo">Evaluación de Calidad Asistencial - Servicio de Urgencias</div>
            <div class="subtitulo" style="font-size: 1.1em; margin-top: 10px;">Clínica Foianini</div>
            <div class="fecha">📅 {fecha_reporte}</div>
            <div class="periodo">📊 Periodo analizado: {periodo_texto}</div>
        </div>
"""

    # RESUMEN EJECUTIVO
    html += f"""
        <!-- RESUMEN EJECUTIVO -->
        <div class="resumen-grid">
            <div class="tarjeta-resumen">
                <div class="icono">📋</div>
                <div class="etiqueta">Total Atenciones Auditadas</div>
                <div class="valor">{analisis['total']}</div>
                <div class="detalle">{analisis['pacientes_unicos']} pacientes únicos evaluados</div>
            </div>

            <div class="tarjeta-resumen">
                <div class="icono">⭐</div>
                <div class="etiqueta">Score Promedio de Calidad</div>
                <div class="valor">{analisis['score_promedio']:.1f}<span style="font-size: 0.5em;">/100</span></div>
                <div class="detalle">Rango: {analisis['score_min']} - {analisis['score_max']} puntos</div>
            </div>

            <div class="tarjeta-resumen">
                <div class="icono">✅</div>
                <div class="etiqueta">Cumplimiento de Guías</div>
                <div class="valor">{(analisis['cumplen']/analisis['total']*100):.1f}%</div>
                <div class="detalle">{analisis['cumplen']} de {analisis['total']} atenciones cumplen</div>
            </div>

            <div class="tarjeta-resumen">
                <div class="icono">👨‍⚕️</div>
                <div class="etiqueta">Médicos Evaluados</div>
                <div class="valor">{len(analisis['medicos'])}</div>
                <div class="detalle">Análisis individual y comparativo</div>
            </div>
        </div>
"""

    # DISTRIBUCIÓN DE SCORES
    html += f"""
        <!-- DISTRIBUCIÓN DE CALIDAD -->
        <div class="seccion">
            <h2>📊 Distribución de Calidad Asistencial</h2>

            <div class="chart-container">
                <div class="bar-chart">
                    <div class="bar-row">
                        <div class="bar-label">⭐⭐⭐ Excelente (80-100)</div>
                        <div class="bar" style="width: {analisis['distribucion_scores']['excelente']/analisis['total']*100}%; background: linear-gradient(90deg, #10b981 0%, #34d399 100%);">
                            <div class="bar-value">{analisis['distribucion_scores']['excelente']} atenciones</div>
                        </div>
                    </div>
                    <div class="bar-row">
                        <div class="bar-label">⭐⭐ Bueno (60-79)</div>
                        <div class="bar" style="width: {analisis['distribucion_scores']['bueno']/analisis['total']*100}%; background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);">
                            <div class="bar-value">{analisis['distribucion_scores']['bueno']} atenciones</div>
                        </div>
                    </div>
                    <div class="bar-row">
                        <div class="bar-label">⭐ Regular (40-59)</div>
                        <div class="bar" style="width: {analisis['distribucion_scores']['regular']/analisis['total']*100}%; background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);">
                            <div class="bar-value">{analisis['distribucion_scores']['regular']} atenciones</div>
                        </div>
                    </div>
                    <div class="bar-row">
                        <div class="bar-label">❌ Deficiente (&lt;40)</div>
                        <div class="bar" style="width: {analisis['distribucion_scores']['deficiente']/analisis['total']*100}%; background: linear-gradient(90deg, #ef4444 0%, #f87171 100%);">
                            <div class="bar-value">{analisis['distribucion_scores']['deficiente']} atenciones</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="info-box info" style="margin-top: 20px;">
                <strong>Interpretación:</strong> El score de calidad del acto médico (0-100) evalúa: diagnóstico oportuno y certero,
                estudios solicitados apropiados al diagnóstico, tratamiento administrado correcto según guías internacionales,
                y cumplimiento de tiempos de atención. NO evalúa calidad de documentación o registros.
            </div>
        </div>
"""

    # GUÍAS CLÍNICAS CON CONTADORES CORREGIDOS
    referencias_who = analisis['guias_por_org']['WHO']
    referencias_aha = analisis['guias_por_org']['AHA']
    referencias_nice = analisis['guias_por_org']['NICE']
    referencias_erc = analisis['guias_por_org']['ERC']
    referencias_acep = analisis['guias_por_org']['ACEP']
    referencias_ascrs = analisis['guias_por_org']['ASCRS']
    referencias_acs = analisis['guias_por_org']['ACS']
    referencias_otras = analisis['guias_por_org']['Otras']

    html += f"""
        <!-- GUÍAS CLÍNICAS -->
        <div class="seccion">
            <h2>📚 Guías Clínicas Internacionales de Referencia</h2>

            <p style="margin-bottom: 20px; color: #475569; font-size: 1.05em;">
                La auditoría evaluó la adherencia a las principales guías clínicas internacionales en medicina de urgencias.
                A continuación se detallan las organizaciones de referencia utilizadas:
            </p>

            <table>
                <thead>
                    <tr>
                        <th style="width: 15%;">Organización</th>
                        <th style="width: 35%;">Descripción</th>
                        <th style="width: 40%;">Áreas Principales</th>
                        <th style="width: 10%; text-align: center;">Referencias</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>WHO</strong><br><span style="font-size: 0.85em; color: #64748b;">World Health Organization</span></td>
                        <td>Organización Mundial de la Salud - Estándares globales en emergencias médicas</td>
                        <td>Triaje, Reanimación, Trauma, Protocolos de emergencia</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_who}</td>
                    </tr>
                    <tr>
                        <td><strong>AHA</strong><br><span style="font-size: 0.85em; color: #64748b;">American Heart Association</span></td>
                        <td>Asociación Americana del Corazón - Líder en emergencias cardiovasculares</td>
                        <td>RCP, ACLS, Síndrome coronario agudo, Arritmias</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_aha}</td>
                    </tr>
                    <tr>
                        <td><strong>NICE</strong><br><span style="font-size: 0.85em; color: #64748b;">National Institute for Health and Care Excellence</span></td>
                        <td>Instituto británico de excelencia en salud</td>
                        <td>Sepsis, Trauma, Dolor agudo, Intoxicaciones</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_nice}</td>
                    </tr>
                    <tr>
                        <td><strong>ERC</strong><br><span style="font-size: 0.85em; color: #64748b;">European Resuscitation Council</span></td>
                        <td>Consejo Europeo de Resucitación</td>
                        <td>Reanimación cardiopulmonar, Soporte vital, Emergencias pediátricas</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_erc}</td>
                    </tr>
                    <tr>
                        <td><strong>ACEP</strong><br><span style="font-size: 0.85em; color: #64748b;">American College of Emergency Physicians</span></td>
                        <td>Colegio Americano de Médicos de Emergencia</td>
                        <td>Dolor torácico, Abdomen agudo, Cefalea, Stroke</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_acep}</td>
                    </tr>
                    <tr>
                        <td><strong>ASCRS</strong><br><span style="font-size: 0.85em; color: #64748b;">American Society of Colon and Rectal Surgeons</span></td>
                        <td>Sociedad Americana de Cirujanos de Colon y Recto</td>
                        <td>Patología anorrectal, Hemorroides, Fisuras, Abscesos</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_ascrs}</td>
                    </tr>
                    <tr>
                        <td><strong>ACS</strong><br><span style="font-size: 0.85em; color: #64748b;">American College of Surgeons</span></td>
                        <td>Colegio Americano de Cirujanos</td>
                        <td>Trauma, Atención quirúrgica de emergencia, ATLS</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_acs}</td>
                    </tr>
"""

    if referencias_otras > 0:
        html += f"""
                    <tr>
                        <td><strong>Otras</strong></td>
                        <td>Guías especializadas adicionales</td>
                        <td>Áreas específicas según patología</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 1.2em;">{referencias_otras}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>

            <div class="info-box info" style="margin-top: 20px;">
                <strong>Nota Metodológica:</strong> La columna "Referencias" indica el número de veces que se aplicaron guías de cada organización
                durante la evaluación. Una misma atención puede requerir múltiples guías según la complejidad del caso.
            </div>
        </div>
"""

    # ANÁLISIS POR MÉDICO
    medicos_ordenados = sorted(
        analisis['medicos'].items(),
        key=lambda x: sum(x[1]['scores']) / len(x[1]['scores']),
        reverse=True
    )

    html += """
        <!-- ANÁLISIS POR MÉDICO -->
        <div class="seccion">
            <h2>👨‍⚕️ Análisis de Desempeño por Médico</h2>

            <p style="margin-bottom: 20px; color: #475569; font-size: 1.05em;">
                Evaluación comparativa del desempeño de cada profesional médico durante el período auditado.
            </p>

            <table>
                <thead>
                    <tr>
                        <th>Médico</th>
                        <th style="text-align: center;">Atenciones</th>
                        <th style="text-align: center;">Score Promedio</th>
                        <th style="text-align: center;">Score Min/Max</th>
                        <th style="text-align: center;">% Cumplimiento</th>
                    </tr>
                </thead>
                <tbody>
"""

    for medico_id, info in medicos_ordenados:
        score_prom = sum(info['scores']) / len(info['scores'])
        score_min = min(info['scores'])
        score_max = max(info['scores'])
        cumplimientos = sum(1 for c in info['cumplimientos'] if c.lower() in ['sí', 'si', 'yes'])
        porcentaje_cump = (cumplimientos / len(info['cumplimientos']) * 100) if info['cumplimientos'] else 0

        # Badge de score
        if score_prom >= 80:
            badge_class = "score-excelente"
        elif score_prom >= 60:
            badge_class = "score-bueno"
        elif score_prom >= 40:
            badge_class = "score-regular"
        else:
            badge_class = "score-deficiente"

        html += f"""
                    <tr>
                        <td><strong>{info['nombre']}</strong></td>
                        <td style="text-align: center;">{len(info['atenciones'])}</td>
                        <td style="text-align: center;"><span class="score-badge {badge_class}">{score_prom:.1f}</span></td>
                        <td style="text-align: center;">{score_min} - {score_max}</td>
                        <td style="text-align: center;"><strong>{porcentaje_cump:.1f}%</strong></td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>
"""

    # TABLA RESUMEN DE ATENCIONES
    html += """
        <!-- TABLA RESUMEN DE ATENCIONES -->
        <div class="seccion">
            <h2>📋 Resumen Ejecutivo de Atenciones</h2>

            <p style="margin-bottom: 15px; color: #475569; font-size: 0.95em;">
                Vista consolidada de todas las atenciones evaluadas. Use los filtros para ver casos específicos por médico.
            </p>

            <!-- BOTONES DE FILTRO - SET 1 -->
            <div id="filtros-tabla" class="filtros-medicos">
"""

    # Insertar botones del Set 1
    html += generar_botones_filtro(analisis)

    html += """
            </div>
            <!-- FIN BOTONES -->

            <div class="tabla-scroll">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 100px;">Fecha</th>
                            <th style="width: 80px;">ID</th>
                            <th style="width: 100px;">Cuenta</th>
                            <th style="width: 150px;">Paciente</th>
                            <th style="width: 200px;">Médico</th>
                            <th style="width: 80px; text-align: center;">Score</th>
                            <th style="width: 180px;">Guías Aplicadas</th>
                            <th style="width: auto;">Resumen de Atención</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for atencion in data:
        score = atencion['score_calidad']

        # Badge de score
        if score >= 80:
            badge_class = "score-excelente"
        elif score >= 60:
            badge_class = "score-bueno"
        elif score >= 40:
            badge_class = "score-regular"
        else:
            badge_class = "score-deficiente"

        # Guías - TODAS las guías sin cortar
        guias_texto = ""
        if atencion['guias_aplicables']:
            guias_list = []
            for g in atencion['guias_aplicables']:
                # Extraer solo el nombre de la organización (ej: "WHO - xxx" -> "WHO")
                org = g.split(' - ')[0] if ' - ' in g else g.split(':')[0] if ':' in g else g[:30]
                guias_list.append(f"• {org}")
            guias_texto = "<br>".join(guias_list)
        else:
            guias_texto = "<em>No especificado</em>"

        # Resumen de atención COMPLETO - sin cortar y sin "Dx:"
        resumen_atencion = atencion.get('comentarios_adicionales', atencion['diagnostico_urgencia'])
        if not resumen_atencion or resumen_atencion.strip() == "":
            resumen_atencion = atencion['diagnostico_urgencia']

        # Formatear cuenta (Gestión/Internación)
        cuenta_formato = f"{atencion.get('cuenta_gestion', 'N/A')}/{atencion.get('cuenta_internacion', 'N/A')}"

        # Nombre del paciente
        nombre_paciente = atencion.get('nombre_paciente', 'No especificado')

        html += f"""
                    <tr data-medico-id="{atencion['id_medico']}" data-medico-nombre="{atencion['nombre_medico']}">
                        <td style="font-size: 0.8em;">{atencion['fecha_atencion'].split(' ')[0]}<br><span style="color: #64748b;">{atencion['fecha_atencion'].split(' ')[1] if len(atencion['fecha_atencion'].split(' ')) > 1 else ''}</span></td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af; font-size: 0.85em;">{atencion['id_evolucion']}</td>
                        <td style="font-size: 0.8em; font-weight: 500; color: #1e40af;">{cuenta_formato}</td>
                        <td style="font-size: 0.8em;">{nombre_paciente}</td>
                        <td style="font-size: 0.8em;">{atencion['nombre_medico']}</td>
                        <td style="text-align: center;"><span class="score-badge {badge_class}" style="font-size: 0.8em; padding: 4px 10px;">{score}</span></td>
                        <td style="font-size: 0.8em; line-height: 1.4;">{guias_texto}</td>
                        <td style="font-size: 0.85em; line-height: 1.6;">{resumen_atencion}</td>
                    </tr>
"""

    html += """
                </tbody>
                </table>
            </div>
        </div>
"""

    # DETALLE DE ATENCIONES
    html += """
        <!-- DETALLE DE ATENCIONES -->
        <div class="seccion">
            <h2>📄 Detalle de Atenciones Auditadas</h2>

            <p style="margin-bottom: 20px; color: #475569; font-size: 1.05em;">
                Revisión detallada de cada caso. Use los filtros para enfocarse en un médico específico.
            </p>

            <!-- BOTONES DE FILTRO - SET 2 -->
            <div id="filtros-detalle" class="filtros-medicos">
"""

    # Insertar botones del Set 2
    html += generar_botones_filtro(analisis)

    html += """
            </div>
            <!-- FIN BOTONES -->
"""

    for i, atencion in enumerate(data, 1):
        score = atencion['score_calidad']

        # Badge y color según score
        if score >= 80:
            badge_class = "score-excelente"
            progress_color = "#10b981"
        elif score >= 60:
            badge_class = "score-bueno"
            progress_color = "#3b82f6"
        elif score >= 40:
            badge_class = "score-regular"
            progress_color = "#f59e0b"
        else:
            badge_class = "score-deficiente"
            progress_color = "#ef4444"

        cuenta_formato = f"{atencion.get('cuenta_gestion', 'N/A')}/{atencion.get('cuenta_internacion', 'N/A')}"
        nombre_paciente = atencion.get('nombre_paciente', 'No especificado')

        html += f"""
            <div class="atencion-card" data-medico-id="{atencion['id_medico']}">
                <div class="atencion-header">
                    <div>
                        <h3 style="margin: 0; color: #1e40af;">Caso #{i} - {atencion['nombre_medico']}</h3>
                        <div class="atencion-meta">
                            📅 {atencion['fecha_atencion']} |
                            👤 Paciente: {nombre_paciente} |
                            🏥 Cuenta: {cuenta_formato} |
                            📋 Evolución: {atencion['id_evolucion']}
                        </div>
                    </div>
                    <div>
                        <span class="score-badge {badge_class}" style="font-size: 1.2em;">{score} pts</span>
                    </div>
                </div>

                <div style="margin: 15px 0;">
                    <strong style="color: #1e40af;">Diagnóstico:</strong> {atencion['diagnostico_urgencia']}
                </div>

                <div style="margin: 15px 0;">
                    <strong style="color: #64748b; font-size: 0.9em;">Progreso de Calidad:</strong>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {score}%; background: {progress_color};"></div>
                    </div>
                </div>

                <div style="margin: 20px 0;">
                    <h4 style="color: #1e40af; margin-bottom: 10px;">📚 Guías Aplicables</h4>
                    <ul style="margin-left: 25px; color: #475569;">
"""

        for guia in atencion['guias_aplicables']:
            html += f"                        <li>{guia}</li>\n"

        html += """
                    </ul>
                </div>

                <div class="criterios-grid">
                    <div class="criterios-columna criterios-cumplidos">
                        <h4>✅ Criterios Cumplidos</h4>
                        <ul>
"""

        if atencion['criterios_cumplidos']:
            for criterio in atencion['criterios_cumplidos']:
                html += f"                            <li>{criterio}</li>\n"
        else:
            html += "                            <li><em>No se registraron criterios cumplidos</em></li>\n"

        html += """
                        </ul>
                    </div>

                    <div class="criterios-columna criterios-no-cumplidos">
                        <h4>❌ Criterios No Cumplidos</h4>
                        <ul>
"""

        if atencion['criterios_no_cumplidos']:
            for criterio in atencion['criterios_no_cumplidos']:
                html += f"                            <li>{criterio}</li>\n"
        else:
            html += "                            <li><em>Todos los criterios fueron cumplidos</em></li>\n"

        html += """
                        </ul>
                    </div>
                </div>

                <div style="margin: 20px 0;">
                    <h4 style="color: #1e40af; margin-bottom: 10px;">🔍 Evaluaciones Específicas</h4>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px;">
"""

        # Evaluación de tratamiento
        tratamiento_icon = "✅" if "adecuado" in atencion.get('tratamiento_adecuado', '').lower() or "sí" in atencion.get('tratamiento_adecuado', '').lower() else "⚠️"
        html += f"""
                        <div style="padding: 12px; background: #f8fafc; border-radius: 6px; border-left: 3px solid #3b82f6;">
                            <strong style="color: #64748b; font-size: 0.9em;">💊 Tratamiento:</strong><br>
                            <span style="color: #1e293b;">{tratamiento_icon} {atencion.get('tratamiento_adecuado', 'No especificado')}</span>
                        </div>
"""

        # Evaluación de tiempo
        tiempo_icon = "✅" if "adecuado" in atencion.get('tiempo_atencion', '').lower() or "normal" in atencion.get('tiempo_atencion', '').lower() else "⚠️"
        html += f"""
                        <div style="padding: 12px; background: #f8fafc; border-radius: 6px; border-left: 3px solid #3b82f6;">
                            <strong style="color: #64748b; font-size: 0.9em;">⏱️ Tiempo de Atención:</strong><br>
                            <span style="color: #1e293b;">{tiempo_icon} {atencion.get('tiempo_atencion', 'No especificado')}</span>
                        </div>
"""

        # Evaluación de estudios
        estudios_icon = "✅" if "apropiado" in atencion.get('estudios_solicitados', '').lower() or "adecuado" in atencion.get('estudios_solicitados', '').lower() else "⚠️"
        html += f"""
                        <div style="padding: 12px; background: #f8fafc; border-radius: 6px; border-left: 3px solid #3b82f6;">
                            <strong style="color: #64748b; font-size: 0.9em;">🔬 Estudios Solicitados:</strong><br>
                            <span style="color: #1e293b;">{estudios_icon} {atencion.get('estudios_solicitados', 'No especificado')}</span>
                        </div>
"""

        # Evaluación de medicación
        medicacion_icon = "✅" if "apropiada" in atencion.get('medicacion_apropiada', '').lower() or "adecuada" in atencion.get('medicacion_apropiada', '').lower() else "⚠️"
        html += f"""
                        <div style="padding: 12px; background: #f8fafc; border-radius: 6px; border-left: 3px solid #3b82f6;">
                            <strong style="color: #64748b; font-size: 0.9em;">💉 Medicación:</strong><br>
                            <span style="color: #1e293b;">{medicacion_icon} {atencion.get('medicacion_apropiada', 'No especificado')}</span>
                        </div>
"""

        html += """
                    </div>
                </div>
"""

        # Hallazgos críticos
        if atencion.get('hallazgos_criticos') and len(atencion['hallazgos_criticos']) > 0:
            html += """
                <div class="info-box critico">
                    <h4 style="margin-bottom: 10px; color: #991b1b;">🚨 Hallazgos Críticos</h4>
                    <ul style="margin-left: 20px;">
"""
            for hallazgo in atencion['hallazgos_criticos']:
                html += f"                        <li>{hallazgo}</li>\n"

            html += """
                    </ul>
                </div>
"""

        # Recomendaciones
        if atencion.get('recomendaciones') and len(atencion['recomendaciones']) > 0:
            html += """
                <div class="info-box info">
                    <h4 style="margin-bottom: 10px; color: #1e40af;">💡 Recomendaciones</h4>
                    <ol style="margin-left: 25px;">
"""
            for recomendacion in atencion['recomendaciones']:
                html += f"                        <li>{recomendacion}</li>\n"

            html += """
                    </ol>
                </div>
"""

        # Comentarios adicionales
        if atencion.get('comentarios_adicionales') and atencion['comentarios_adicionales'].strip():
            html += f"""
                <div style="margin-top: 15px; padding: 12px; background: #f1f5f9; border-radius: 6px; border-left: 3px solid #64748b;">
                    <strong style="color: #64748b;">📝 Comentarios del Auditor:</strong><br>
                    <span style="color: #475569; font-style: italic;">{atencion['comentarios_adicionales']}</span>
                </div>
"""

        html += """
            </div>
"""

    html += """
        </div>
"""

    # HALLAZGOS CRÍTICOS GLOBALES
    html += """
        <!-- HALLAZGOS CRÍTICOS GLOBALES -->
        <div class="seccion">
            <h2>🚨 Hallazgos Críticos Más Frecuentes</h2>

            <p style="margin-bottom: 20px; color: #475569; font-size: 1.05em;">
                Top 10 de hallazgos críticos identificados durante la auditoría, ordenados por frecuencia de aparición.
            </p>
"""

    hallazgos_top = analisis['hallazgos'].most_common(10)

    if hallazgos_top:
        html += """
            <table>
                <thead>
                    <tr>
                        <th style="width: 10%; text-align: center;">#</th>
                        <th style="width: 60%;">Hallazgo Crítico</th>
                        <th style="width: 15%; text-align: center;">Frecuencia</th>
                        <th style="width: 15%; text-align: center;">% del Total</th>
                    </tr>
                </thead>
                <tbody>
"""

        total_hallazgos = sum(analisis['hallazgos'].values())

        for idx, (hallazgo, count) in enumerate(hallazgos_top, 1):
            porcentaje = (count / total_hallazgos * 100) if total_hallazgos > 0 else 0
            html += f"""
                    <tr>
                        <td style="text-align: center; font-weight: 600; color: #dc2626;">{idx}</td>
                        <td>{hallazgo}</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af;">{count}</td>
                        <td style="text-align: center;">{porcentaje:.1f}%</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
"""
    else:
        html += """
            <div class="info-box exito">
                <strong>✅ Excelente:</strong> No se identificaron hallazgos críticos durante el período auditado.
            </div>
"""

    html += """
        </div>
"""

    # RECOMENDACIONES PRIORITARIAS
    html += """
        <!-- RECOMENDACIONES PRIORITARIAS -->
        <div class="seccion">
            <h2>💡 Recomendaciones Prioritarias</h2>

            <p style="margin-bottom: 20px; color: #475569; font-size: 1.05em;">
                Top 10 de recomendaciones más frecuentes basadas en los hallazgos de la auditoría.
            </p>
"""

    recomendaciones_top = analisis['recomendaciones'].most_common(10)

    if recomendaciones_top:
        html += """
            <table>
                <thead>
                    <tr>
                        <th style="width: 10%; text-align: center;">#</th>
                        <th style="width: 60%;">Recomendación</th>
                        <th style="width: 15%; text-align: center;">Frecuencia</th>
                        <th style="width: 15%; text-align: center;">% del Total</th>
                    </tr>
                </thead>
                <tbody>
"""

        total_recomendaciones = sum(analisis['recomendaciones'].values())

        for idx, (recomendacion, count) in enumerate(recomendaciones_top, 1):
            porcentaje = (count / total_recomendaciones * 100) if total_recomendaciones > 0 else 0
            html += f"""
                    <tr>
                        <td style="text-align: center; font-weight: 600; color: #3b82f6;">{idx}</td>
                        <td>{recomendacion}</td>
                        <td style="text-align: center; font-weight: 600; color: #1e40af;">{count}</td>
                        <td style="text-align: center;">{porcentaje:.1f}%</td>
                    </tr>
"""

        html += """
                </tbody>
            </table>
"""
    else:
        html += """
            <div class="info-box info">
                <strong>Nota:</strong> No se registraron recomendaciones específicas durante el período auditado.
            </div>
"""

    html += """
        </div>
"""

    # CONCLUSIONES Y NEXT STEPS
    html += f"""
        <!-- CONCLUSIONES Y NEXT STEPS -->
        <div class="seccion">
            <h2>🎯 Conclusiones y Plan de Acción</h2>

            <h3>Puntos Fuertes Identificados</h3>
            <div class="info-box exito">
                <ul style="margin-left: 25px; line-height: 1.8;">
"""

    # Generar puntos fuertes dinámicamente
    if analisis['score_promedio'] >= 70:
        html += f"                    <li><strong>Score promedio de calidad de {analisis['score_promedio']:.1f}</strong>, indicando un nivel de atención por encima del estándar aceptable.</li>\n"

    if (analisis['cumplen'] / analisis['total'] * 100) >= 70:
        html += f"                    <li><strong>Alto cumplimiento de guías clínicas ({(analisis['cumplen']/analisis['total']*100):.1f}%)</strong>, demostrando adherencia a estándares internacionales.</li>\n"

    if analisis['distribucion_scores']['excelente'] > 0:
        html += f"                    <li><strong>{analisis['distribucion_scores']['excelente']} atenciones clasificadas como excelentes</strong> (score ≥ 80), mostrando capacidad del equipo para brindar atención de alta calidad.</li>\n"

    # Identificar mejor médico
    if medicos_ordenados:
        mejor_medico = medicos_ordenados[0]
        mejor_score = sum(mejor_medico[1]['scores']) / len(mejor_medico[1]['scores'])
        html += f"                    <li><strong>Desempeño destacado del Dr./Dra. {mejor_medico[1]['nombre']}</strong> con score promedio de {mejor_score:.1f}.</li>\n"

    html += """
                    <li><strong>Uso de guías clínicas internacionales de prestigio</strong> (WHO, AHA, NICE, etc.) como referencia en la atención.</li>
                </ul>
            </div>

            <h3>Áreas de Mejora Prioritarias</h3>
            <div class="info-box advertencia">
                <ul style="margin-left: 25px; line-height: 1.8;">
"""

    # Generar áreas de mejora dinámicamente
    if analisis['distribucion_scores']['deficiente'] > 0:
        html += f"                    <li><strong>Atención a casos con score deficiente:</strong> {analisis['distribucion_scores']['deficiente']} atenciones requieren revisión y mejora inmediata.</li>\n"

    if (analisis['cumplen'] / analisis['total'] * 100) < 70:
        html += f"                    <li><strong>Mejorar adherencia a guías clínicas:</strong> Actualmente en {(analisis['cumplen']/analisis['total']*100):.1f}%, objetivo: alcanzar ≥ 85%.</li>\n"

    if hallazgos_top and len(hallazgos_top) > 0:
        hallazgo_principal = hallazgos_top[0][0]
        html += f"                    <li><strong>Atender hallazgo crítico más frecuente:</strong> {hallazgo_principal}.</li>\n"

    if analisis['distribucion_scores']['regular'] > 0:
        html += f"                    <li><strong>Elevar casos con desempeño regular:</strong> {analisis['distribucion_scores']['regular']} atenciones en rango 40-59 requieren capacitación específica.</li>\n"

    html += """
                    <li><strong>Estandarización de documentación clínica</strong> para asegurar trazabilidad completa de decisiones médicas.</li>
                </ul>
            </div>

            <h3>Recomendaciones de Seguimiento</h3>
            <div class="info-box info">
                <ol style="margin-left: 25px; line-height: 1.8;">
                    <li><strong>Sesiones de capacitación continua:</strong> Implementar talleres mensuales sobre guías clínicas actualizadas, enfocándose en las áreas con mayores hallazgos críticos.</li>
                    <li><strong>Auditorías médicas periódicas:</strong> Establecer un ciclo de revisión trimestral para monitorear tendencias y evaluar impacto de acciones correctivas.</li>
                    <li><strong>Feedback individualizado:</strong> Programar sesiones uno a uno con cada médico para revisar casos específicos y oportunidades de mejora.</li>
                    <li><strong>Protocolos institucionales:</strong> Desarrollar o actualizar protocolos internos basados en las guías internacionales más aplicadas.</li>
                    <li><strong>Sistema de alertas clínicas:</strong> Implementar recordatorios automáticos en el sistema de historias clínicas para criterios críticos de las guías.</li>
                    <li><strong>Benchmarking:</strong> Comparar resultados con estándares internacionales y hospitales de referencia para identificar gaps específicos.</li>
                    <li><strong>Programa de mentoría:</strong> Establecer sistema de acompañamiento donde médicos con mejor desempeño apoyen a colegas en desarrollo.</li>
                    <li><strong>Monitoreo de indicadores clave:</strong> Seguimiento mensual de score promedio, cumplimiento de guías y hallazgos críticos.</li>
                </ol>
            </div>

            <div class="info-box exito" style="margin-top: 25px;">
                <h4 style="margin-bottom: 10px; color: #065f46;">✅ Próximos Pasos Inmediatos (30 días)</h4>
                <ul style="margin-left: 25px;">
                    <li>Socializar resultados de esta auditoría con todo el equipo médico</li>
                    <li>Identificar y contactar casos para revisión detallada (scores &lt; 40)</li>
                    <li>Programar primera sesión de capacitación sobre hallazgos más frecuentes</li>
                    <li>Establecer comité de calidad para dar seguimiento a recomendaciones</li>
                    <li>Definir métricas de éxito y cronograma de re-evaluación</li>
                </ul>
            </div>
        </div>
"""

    # FOOTER
    html += f"""
        <!-- FOOTER -->
        <div class="footer">
            <div class="footer-divider"></div>
            <p style="font-size: 1.1em; color: #1e40af; font-weight: 600; margin-bottom: 10px;">Clínica Foianini</p>
            <p>Auditoría Médica - Servicio de Urgencias</p>
            <p style="margin-top: 15px; color: #64748b;">
                <strong>Fecha de generación:</strong> {datetime.now().strftime("%d de %B de %Y a las %H:%M hrs")}
            </p>
            <p style="margin-top: 10px; font-size: 0.85em; color: #94a3b8;">
                Documento confidencial - Solo para uso interno de la institución
            </p>
        </div>

    </div>

    <!-- JavaScript para filtrado por médico -->
    <script>
    function filtrarPorMedico(medicoId) {{
        // Actualizar todos los botones (ambos sets)
        document.querySelectorAll('.btn-filtro').forEach(btn => {{
            btn.classList.remove('active');
        }});
        document.querySelectorAll(`[data-medico-id="${{medicoId}}"]`).forEach(btn => {{
            if (btn.classList.contains('btn-filtro')) {{
                btn.classList.add('active');
            }}
        }});

        // Filtrar filas de tabla
        const tableRows = document.querySelectorAll('table tbody tr[data-medico-id]');
        tableRows.forEach(row => {{
            if (medicoId === 'todos' || row.dataset.medicoId === medicoId) {{
                row.style.display = '';
            }} else {{
                row.style.display = 'none';
            }}
        }});

        // Filtrar cards de detalle
        const cards = document.querySelectorAll('.atencion-card[data-medico-id]');
        cards.forEach(card => {{
            if (medicoId === 'todos' || card.dataset.medicoId === medicoId) {{
                card.style.display = '';
            }} else {{
                card.style.display = 'none';
            }}
        }});
    }}
    </script>
</body>
</html>
"""

    return html

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python generar_reporte_v2.py <archivo_jsonl>")
        sys.exit(1)

    archivo_entrada = sys.argv[1]

    try:
        print("Cargando datos...")
        data = cargar_datos(archivo_entrada)
        print(f"  [OK] {len(data)} atenciones cargadas")

        print("Analizando datos...")
        analisis = analizar_datos(data)
        print(f"  [OK] Análisis completado")

        # Generar nombre de archivo de salida
        archivo_salida = archivo_entrada.replace('.jsonl', '.html')

        print("Generando reporte HTML...")
        html = generar_html(data, analisis, archivo_salida)

        # Escribir archivo HTML
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n{'='*60}")
        print(f"REPORTE GENERADO EXITOSAMENTE")
        print(f"{'='*60}")
        print(f"Archivo: {archivo_salida}")
        print(f"Estadisticas:")
        print(f"   - Total de atenciones: {analisis['total']}")
        print(f"   - Score promedio: {analisis['score_promedio']:.1f}")
        print(f"   - Cumplimiento de guias: {(analisis['cumplen']/analisis['total']*100):.1f}%")
        print(f"   - Medicos evaluados: {len(analisis['medicos'])}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

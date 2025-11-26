"""
Auditor de Atención Específica - Clínica Foianini
==================================================

Script para auditar una atención individual proporcionando su número de cuenta.

Uso:
    python auditar_atencion.py 2025/140954
    python auditar_atencion.py --gestion 2025 --internacion 140954
    python auditar_atencion.py  (modo interactivo)

Outputs:
    - JSON: output/atencion_[gestion]_[internacion]_YYYYMMDD_HHMMSS.json
    - HTML: output/atencion_[gestion]_[internacion]_YYYYMMDD_HHMMSS.html
    - Resumen en consola

Autor: Sistema de Auditoría Médica
Fecha: Noviembre 2025
"""

import sys
import json
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Importar componentes reutilizables del main.py
from main import (
    MCPClient,
    AuditorLLM,
    AuditoriaUrgenciaResultado,
    formatear_atencion_para_llm
)


class AuditorAtencionEspecifica:
    """Auditor para una atención específica"""

    def __init__(self):
        load_dotenv()
        self.mcp_client = MCPClient()
        self.auditor_llm = AuditorLLM()
        print("✅ Conectado a MySQL y servicios de IA")

    def parsear_cuenta(self, cuenta_str):
        """
        Parsea el formato de cuenta
        Entrada: "2025/140954" o "2025/140954/1"
        Salida: (gestion, internacion, id)
        """
        partes = cuenta_str.split('/')

        if len(partes) < 2:
            raise ValueError(f"Formato de cuenta inválido: '{cuenta_str}'. Use formato: GESTION/INTERNACION (ej: 2025/140954)")

        try:
            gestion = int(partes[0])
            internacion = int(partes[1])
            id = int(partes[2]) if len(partes) > 2 else 1
            return gestion, internacion, id
        except ValueError as e:
            raise ValueError(f"Formato de cuenta inválido: '{cuenta_str}'. Los valores deben ser numéricos.")

    def verificar_atencion_existe(self, gestion, internacion, id):
        """Verifica si la atención existe en la base de datos"""
        detalle = self.mcp_client.get_detalle_atencion(
            persona_numero=0,  # Se obtendrá del query
            cuenta_gestion=gestion,
            cuenta_internacion=internacion,
            cuenta_id=id
        )

        if not detalle or not detalle.get('evoluciones_clinicas'):
            return False, None

        return True, detalle

    def obtener_informacion_basica(self, gestion, internacion):
        """Obtiene información básica de la atención (médico, paciente, fecha)"""
        # Query simplificada sin tabla de diagnósticos
        query = f"""
        SELECT
            pe.PersonaNumero AS id_persona_paciente,
            MIN(pe.PacienteEvolucionFechaHora) AS fecha_atencion,
            (SELECT u2.UsuarioPersonaCodigo
             FROM pacienteevolucion pe2
             LEFT JOIN usuario u2 ON u2.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
             WHERE pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
               AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
             ORDER BY pe2.PacienteEvolucionFechaHora ASC
             LIMIT 1) AS id_medico,
            (SELECT med2.PersonaNombreCompleto
             FROM pacienteevolucion pe2
             LEFT JOIN usuario u2 ON u2.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
             LEFT JOIN persona med2 ON med2.PersonaNumero = u2.UsuarioPersonaCodigo
             WHERE pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
               AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
             ORDER BY pe2.PacienteEvolucionFechaHora ASC
             LIMIT 1) AS nombre_medico,
            pac.PersonaNombreCompleto AS nombre_paciente
        FROM pacienteevolucion pe
        LEFT JOIN persona pac ON pac.PersonaNumero = pe.PersonaNumero
        WHERE pe.PacienteEvolucionGestion = {gestion}
          AND pe.PacienteEvolucionNroInter = {internacion}
          AND pe.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
        GROUP BY
            pe.PersonaNumero,
            pac.PersonaNombreCompleto,
            pe.PacienteEvolucionGestion,
            pe.PacienteEvolucionNroInter
        LIMIT 1
        """

        result = self.mcp_client._execute_query(query)

        if not result or len(result) == 0:
            return None

        return result[0]

    def auditar(self, gestion, internacion, id=1):
        """Ejecuta la auditoría completa de una atención específica"""

        cuenta_formato = f"{gestion}/{internacion}"
        print(f"\n{'='*80}")
        print(f"AUDITORÍA DE ATENCIÓN ESPECÍFICA")
        print(f"{'='*80}")
        print(f"📋 Cuenta: {cuenta_formato}")
        print()

        # Paso 1: Obtener información básica
        print("🔍 Obteniendo información de la atención...")
        info_basica = self.obtener_informacion_basica(gestion, internacion)

        if not info_basica:
            print(f"❌ ERROR: No se encontró la cuenta {cuenta_formato}")
            print("\n💡 Verifique que:")
            print("   • La gestión sea correcta (ej: 2025)")
            print("   • El número de internación sea correcto")
            print("   • La atención esté registrada en el sistema")
            return None

        persona_numero = info_basica['id_persona_paciente']
        nombre_paciente = info_basica['nombre_paciente']
        nombre_medico = info_basica['nombre_medico']
        id_medico = info_basica['id_medico']
        fecha_atencion = str(info_basica['fecha_atencion'])

        print(f"  ✅ Atención encontrada")
        print(f"  👤 Paciente: {nombre_paciente}")
        print(f"  👨‍⚕️ Médico: {nombre_medico}")
        print(f"  📅 Fecha: {fecha_atencion}")
        print()

        # Paso 2: Obtener detalle completo
        print("📄 Obteniendo historial clínico completo...")
        detalle = self.mcp_client.get_detalle_atencion(
            persona_numero=persona_numero,
            cuenta_gestion=gestion,
            cuenta_internacion=internacion,
            cuenta_id=id
        )

        if not detalle or not detalle.get('evoluciones_clinicas'):
            print(f"⚠️  ADVERTENCIA: La cuenta {cuenta_formato} no tiene evoluciones registradas")
            print("   No se puede realizar la auditoría sin datos clínicos")
            return None

        # Contar evoluciones
        evoluciones_raw = detalle.get('evoluciones_clinicas', '')
        num_evoluciones = evoluciones_raw.count('---EVOLUCION---') + 1 if evoluciones_raw else 0

        print(f"  ✅ Historial obtenido")
        print(f"  📋 Evoluciones registradas: {num_evoluciones}")
        print()

        # Paso 3: Formatear para LLM
        historial_formateado = formatear_atencion_para_llm(detalle)

        # Paso 4: Auditar con IA
        print("🤖 Ejecutando auditoría con IA (Claude Sonnet 4.5)...")
        print("   ⏳ Esto puede tomar 30-60 segundos...")
        print()

        # Extraer diagnósticos del historial formateado si están disponibles
        diagnosticos = "Diagnóstico de urgencia - Ver evoluciones clínicas"

        resultado = self.auditor_llm.auditar_atencion(
            historial=historial_formateado,
            id_evolucion=0,  # No relevante para atención individual
            fecha_atencion=fecha_atencion,
            diagnostico=diagnosticos,
            id_persona=persona_numero,
            id_medico=id_medico,
            nombre_medico=nombre_medico,
            nombre_paciente=nombre_paciente,
            cuenta_gestion=gestion,
            cuenta_internacion=internacion
        )

        if not resultado:
            print(f"❌ ERROR: Falló la auditoría con IA")
            print("\n💡 Verifique:")
            print("   • API key de OpenRouter válida en .env")
            print("   • Conectividad a internet")
            print("   • Saldo disponible en OpenRouter")
            return None

        print(f"  ✅ Auditoría completada")
        print(f"  📊 Score de calidad: {resultado.score_calidad}/100")
        print(f"  {'✅' if resultado.cumple_guias.lower() in ['sí', 'si'] else '❌'} Cumple guías: {resultado.cumple_guias}")
        print()

        # Paso 5: Generar outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON
        json_filename = f"output/atencion_{gestion}_{internacion}_{timestamp}.json"
        self.generar_json(resultado, detalle, num_evoluciones, json_filename)
        print(f"  💾 JSON generado: {json_filename}")

        # HTML
        html_filename = f"output/atencion_{gestion}_{internacion}_{timestamp}.html"
        self.generar_html(resultado, detalle, num_evoluciones, html_filename)
        print(f"  📄 HTML generado: {html_filename}")
        print()

        # Mostrar resumen en consola
        self.mostrar_resumen_consola(resultado)

        return resultado

    def generar_json(self, resultado: AuditoriaUrgenciaResultado, detalle: dict, num_evoluciones: int, archivo: str):
        """Genera archivo JSON con metadata completa"""

        data = {
            "metadata": {
                "cuenta": f"{resultado.cuenta_gestion}/{resultado.cuenta_internacion}",
                "fecha_auditoria": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "script_version": "1.0.0",
                "num_evoluciones": num_evoluciones
            },
            "atencion": resultado.model_dump(),
            "historial_clinico": {
                "evoluciones_clinicas": detalle.get('evoluciones_clinicas', ''),
                "signos_vitales": detalle.get('signos_vitales', ''),
                "medicamentos": detalle.get('ejecuciones_medicamentos', ''),
                "laboratorios": detalle.get('laboratorios', ''),
                "estudios_imagen": detalle.get('estudios_imagen', ''),
                "notas_enfermeria": detalle.get('notas_enfermeria', '')
            }
        }

        os.makedirs("output", exist_ok=True)
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generar_html(self, resultado: AuditoriaUrgenciaResultado, detalle: dict, num_evoluciones: int, archivo: str):
        """Genera HTML individual de la atención"""

        score = resultado.score_calidad

        # Determinar badge y color
        if score >= 80:
            badge_class = "excelente"
            progress_color = "#10b981"
            badge_text = "Excelente"
        elif score >= 60:
            badge_class = "bueno"
            progress_color = "#3b82f6"
            badge_text = "Bueno"
        elif score >= 40:
            badge_class = "regular"
            progress_color = "#f59e0b"
            badge_text = "Regular"
        else:
            badge_class = "deficiente"
            progress_color = "#ef4444"
            badge_text = "Deficiente"

        # Formatear cuenta
        cuenta_formato = f"{resultado.cuenta_gestion}/{resultado.cuenta_internacion}"

        # Fecha de auditoría
        fecha_auditoria = datetime.now().strftime("%d de %B de %Y - %H:%M")

        # Traducir mes
        meses = {
            'January': 'enero', 'February': 'febrero', 'March': 'marzo',
            'April': 'abril', 'May': 'mayo', 'June': 'junio',
            'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
            'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
        }
        for en, es in meses.items():
            fecha_auditoria = fecha_auditoria.replace(en, es)

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auditoría Atención {cuenta_formato} | Clínica Foianini</title>
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
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* Portada */
        .portada {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 8px 20px rgba(30, 64, 175, 0.3);
            margin-bottom: 20px;
        }}

        .portada h1 {{
            font-size: 1.8em;
            margin-bottom: 10px;
        }}

        .portada .subtitulo {{
            font-size: 1em;
            opacity: 0.95;
            margin-bottom: 15px;
        }}

        .portada .cuenta {{
            font-size: 1.5em;
            font-weight: 700;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            display: inline-block;
            margin: 10px 0;
        }}

        .portada .fecha {{
            font-size: 0.85em;
            opacity: 0.9;
        }}

        /* Card principal */
        .card {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 6px rgba(30, 64, 175, 0.08);
        }}

        .card h2 {{
            color: #1e40af;
            font-size: 1.5em;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #3b82f6;
        }}

        /* Score badge */
        .score-badge {{
            display: inline-block;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 2em;
            font-weight: 700;
            margin: 20px 0;
        }}

        .score-badge.excelente {{
            background: #d1fae5;
            color: #065f46;
        }}

        .score-badge.bueno {{
            background: #dbeafe;
            color: #1e40af;
        }}

        .score-badge.regular {{
            background: #fed7aa;
            color: #92400e;
        }}

        .score-badge.deficiente {{
            background: #fee2e2;
            color: #991b1b;
        }}

        /* Info grid */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}

        .info-item {{
            padding: 15px;
            background: #f8fafc;
            border-radius: 6px;
            border-left: 3px solid #3b82f6;
        }}

        .info-item .label {{
            font-size: 0.85em;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}

        .info-item .value {{
            font-size: 1em;
            color: #1e293b;
            font-weight: 500;
        }}

        /* Progress bar */
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e2e8f0;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: {progress_color};
            border-radius: 15px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 15px;
            color: white;
            font-weight: 600;
        }}

        /* Listas */
        .criterios-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}

        .criterios-columna {{
            padding: 20px;
            border-radius: 8px;
        }}

        .criterios-cumplidos {{
            background: #f0fdf4;
            border: 2px solid #86efac;
        }}

        .criterios-no-cumplidos {{
            background: #fef2f2;
            border: 2px solid #fca5a5;
        }}

        .criterios-columna h3 {{
            margin-bottom: 15px;
            font-size: 1.2em;
        }}

        .criterios-cumplidos h3 {{
            color: #166534;
        }}

        .criterios-no-cumplidos h3 {{
            color: #991b1b;
        }}

        .criterios-columna ul {{
            margin-left: 20px;
        }}

        .criterios-columna li {{
            margin: 8px 0;
        }}

        /* Sección de historial */
        .historial {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}

        .historial h3 {{
            color: #1e40af;
            margin-bottom: 15px;
        }}

        .historial pre {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border-left: 3px solid #3b82f6;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 0.9em;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            color: #64748b;
            font-size: 0.9em;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- PORTADA -->
        <div class="portada">
            <h1>🏥 Auditoría Individual de Atención</h1>
            <div class="subtitulo">Clínica Foianini - Servicio de Urgencias</div>
            <div class="cuenta">📋 {cuenta_formato}</div>
            <div class="fecha">📅 Fecha de auditoría: {fecha_auditoria}</div>
        </div>

        <!-- RESUMEN EJECUTIVO -->
        <div class="card">
            <h2>📊 Resumen Ejecutivo</h2>

            <div style="text-align: center;">
                <div class="score-badge {badge_class}">{score}/100</div>
                <div style="font-size: 1.2em; color: #64748b; margin-bottom: 20px;">{badge_text}</div>
            </div>

            <div class="info-grid">
                <div class="info-item">
                    <div class="label">👨‍⚕️ Médico</div>
                    <div class="value">{resultado.nombre_medico}</div>
                </div>
                <div class="info-item">
                    <div class="label">👤 Paciente</div>
                    <div class="value">{resultado.nombre_paciente}</div>
                </div>
                <div class="info-item">
                    <div class="label">📅 Fecha de Atención</div>
                    <div class="value">{resultado.fecha_atencion}</div>
                </div>
                <div class="info-item">
                    <div class="label">🏥 Cuenta</div>
                    <div class="value">{cuenta_formato}</div>
                </div>
                <div class="info-item">
                    <div class="label">📋 Evoluciones Registradas</div>
                    <div class="value">{num_evoluciones}</div>
                </div>
                <div class="info-item">
                    <div class="label">✅ Cumple Guías</div>
                    <div class="value">{'Sí' if resultado.cumple_guias.lower() in ['sí', 'si'] else 'No'}</div>
                </div>
            </div>

            <div style="margin: 30px 0;">
                <h3 style="color: #1e40af; margin-bottom: 10px;">📋 Diagnóstico</h3>
                <p style="padding: 15px; background: #f8fafc; border-radius: 6px; border-left: 3px solid #3b82f6;">
                    {resultado.diagnostico_urgencia}
                </p>
            </div>

            <div style="margin: 30px 0;">
                <h3 style="color: #1e40af; margin-bottom: 10px;">📈 Progreso de Calidad</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {score}%;">{score}%</div>
                </div>
            </div>
        </div>

        <!-- GUÍAS APLICABLES -->
        <div class="card">
            <h2>📚 Guías Clínicas Aplicables</h2>
            <ul style="margin-left: 25px; line-height: 2;">
"""

        for guia in resultado.guias_aplicables:
            html += f"                <li><strong>{guia}</strong></li>\n"

        html += """
            </ul>
        </div>

        <!-- CRITERIOS -->
        <div class="card">
            <h2>📋 Evaluación de Criterios</h2>

            <div class="criterios-grid">
                <div class="criterios-columna criterios-cumplidos">
                    <h3>✅ Criterios Cumplidos</h3>
                    <ul>
"""

        if resultado.criterios_cumplidos:
            for criterio in resultado.criterios_cumplidos:
                html += f"                        <li>{criterio}</li>\n"
        else:
            html += "                        <li><em>No se registraron criterios cumplidos</em></li>\n"

        html += """
                    </ul>
                </div>

                <div class="criterios-columna criterios-no-cumplidos">
                    <h3>❌ Criterios No Cumplidos</h3>
                    <ul>
"""

        if resultado.criterios_no_cumplidos:
            for criterio in resultado.criterios_no_cumplidos:
                html += f"                        <li>{criterio}</li>\n"
        else:
            html += "                        <li><em>Todos los criterios fueron cumplidos</em></li>\n"

        html += """
                    </ul>
                </div>
            </div>
        </div>
"""

        # Hallazgos críticos
        if resultado.hallazgos_criticos and len(resultado.hallazgos_criticos) > 0:
            html += """
        <!-- HALLAZGOS CRÍTICOS -->
        <div class="card" style="border-left: 5px solid #ef4444;">
            <h2 style="color: #991b1b;">🚨 Hallazgos Críticos</h2>
            <ol style="margin-left: 25px; line-height: 2;">
"""
            for hallazgo in resultado.hallazgos_criticos:
                html += f"                <li>{hallazgo}</li>\n"

            html += """
            </ol>
        </div>
"""

        # Recomendaciones
        if resultado.recomendaciones and len(resultado.recomendaciones) > 0:
            html += """
        <!-- RECOMENDACIONES -->
        <div class="card" style="border-left: 5px solid #3b82f6;">
            <h2>💡 Recomendaciones</h2>
            <ol style="margin-left: 25px; line-height: 2;">
"""
            for recomendacion in resultado.recomendaciones:
                html += f"                <li>{recomendacion}</li>\n"

            html += """
            </ol>
        </div>
"""

        # Comentarios adicionales
        if resultado.comentarios_adicionales and resultado.comentarios_adicionales.strip():
            html += f"""
        <!-- COMENTARIOS DEL AUDITOR -->
        <div class="card">
            <h2>📝 Comentarios del Auditor</h2>
            <p style="line-height: 1.8; color: #475569; padding: 15px; background: #f8fafc; border-radius: 6px; font-style: italic;">
                {resultado.comentarios_adicionales}
            </p>
        </div>
"""

        # Historial clínico (opcional, colapsado)
        evoluciones = detalle.get('evoluciones_clinicas', '')
        if evoluciones:
            html += f"""
        <!-- HISTORIAL CLÍNICO COMPLETO -->
        <div class="card">
            <h2>🩺 Historial Clínico Completo</h2>
            <p style="color: #64748b; margin-bottom: 15px;">
                Evoluciones clínicas registradas ({num_evoluciones} entradas)
            </p>
            <div class="historial">
                <pre>{evoluciones[:5000]}{'...' if len(evoluciones) > 5000 else ''}</pre>
            </div>
        </div>
"""

        html += f"""
        <!-- FOOTER -->
        <div class="footer">
            <p><strong>Clínica Foianini</strong> - Sistema de Auditoría Médica</p>
            <p style="margin-top: 10px; font-size: 0.85em;">
                Documento confidencial - Solo para uso interno de la institución
            </p>
            <p style="margin-top: 5px; font-size: 0.8em; color: #94a3b8;">
                Generado: {fecha_auditoria}
            </p>
        </div>
    </div>
</body>
</html>
"""

        os.makedirs("output", exist_ok=True)
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(html)

    def mostrar_resumen_consola(self, resultado: AuditoriaUrgenciaResultado):
        """Muestra resumen detallado en consola"""

        print(f"{'='*80}")
        print(f"RESUMEN DE AUDITORÍA")
        print(f"{'='*80}")
        print(f"📊 Score de calidad: {resultado.score_calidad}/100")
        print(f"✅ Cumple guías: {resultado.cumple_guias}")
        print(f"📚 Guías aplicables: {len(resultado.guias_aplicables)} ({', '.join(g.split(' -')[0] if ' -' in g else g.split(':')[0] if ':' in g else g[:30] for g in resultado.guias_aplicables[:5])})")
        print(f"✅ Criterios cumplidos: {len(resultado.criterios_cumplidos)}")
        print(f"❌ Criterios no cumplidos: {len(resultado.criterios_no_cumplidos)}")
        print(f"🚨 Hallazgos críticos: {len(resultado.hallazgos_criticos)}")
        print(f"💡 Recomendaciones: {len(resultado.recomendaciones)}")
        print(f"{'='*80}")
        print()


def main():
    """Función principal con parseo de argumentos"""

    parser = argparse.ArgumentParser(
        description='Auditor de Atención Específica - Clínica Foianini',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python auditar_atencion.py 2025/140954
  python auditar_atencion.py --gestion 2025 --internacion 140954
  python auditar_atencion.py  (modo interactivo)

Outputs:
  - JSON: output/atencion_[gestion]_[internacion]_YYYYMMDD_HHMMSS.json
  - HTML: output/atencion_[gestion]_[internacion]_YYYYMMDD_HHMMSS.html
  - Resumen en consola
        """
    )

    parser.add_argument(
        'cuenta',
        nargs='?',
        help='Número de cuenta en formato GESTION/INTERNACION (ej: 2025/140954)'
    )
    parser.add_argument(
        '--gestion',
        type=int,
        help='Gestión (año) de la cuenta (ej: 2025)'
    )
    parser.add_argument(
        '--internacion',
        type=int,
        help='Número de internación (ej: 140954)'
    )
    parser.add_argument(
        '--id',
        type=int,
        default=1,
        help='ID de la cuenta (por defecto: 1)'
    )

    args = parser.parse_args()

    try:
        # Inicializar auditor
        auditor = AuditorAtencionEspecifica()

        # Determinar cuenta a auditar
        if args.cuenta:
            # Modo 1: Cuenta en formato "GESTION/INTERNACION"
            gestion, internacion, id = auditor.parsear_cuenta(args.cuenta)
        elif args.gestion and args.internacion:
            # Modo 2: Argumentos separados
            gestion = args.gestion
            internacion = args.internacion
            id = args.id
        else:
            # Modo 3: Interactivo
            print("\n" + "="*80)
            print("Auditoría de Atención Específica - Clínica Foianini")
            print("="*80)
            print()

            cuenta_input = input("Ingrese la cuenta en formato GESTION/INTERNACION (ej: 2025/140954): ").strip()

            if '/' in cuenta_input:
                gestion, internacion, id = auditor.parsear_cuenta(cuenta_input)
            else:
                print("❌ Formato inválido. Use formato: GESTION/INTERNACION (ej: 2025/140954)")
                sys.exit(1)

        # Ejecutar auditoría
        resultado = auditor.auditar(gestion, internacion, id)

        if resultado:
            print("✅ Proceso completado exitosamente")
            print()
            sys.exit(0)
        else:
            print("❌ No se pudo completar la auditoría")
            sys.exit(1)

    except ValueError as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

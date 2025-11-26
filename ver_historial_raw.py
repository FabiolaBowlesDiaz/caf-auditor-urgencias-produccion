"""
Script temporal para ver el historial RAW que se envía a Claude
"""
import os
import sys
from dotenv import load_dotenv
from main import MCPClient, formatear_atencion_para_llm

load_dotenv()

def ver_historial(gestion, internacion, id_cuenta=1):
    """Muestra el historial completo que se envía a Claude"""

    client = MCPClient()

    # Obtener info básica
    query = f"""
    SELECT
        pe.PersonaNumero as persona_numero,
        pe.PacienteEvolucionGestion as cuenta_gestion,
        pe.PacienteEvolucionNroInter as cuenta_internacion,
        pe.PacienteEvolucionNroIntId as cuenta_id
    FROM pacienteevolucion pe
    WHERE pe.PacienteEvolucionGestion = {gestion}
      AND pe.PacienteEvolucionNroInter = {internacion}
      AND pe.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    LIMIT 1
    """

    result = client._execute_query(query)
    if not result:
        print("❌ No se encontró la atención")
        return

    info = result[0]
    persona_numero = info['persona_numero']
    cuenta_id = info['cuenta_id']

    print(f"Obteniendo detalle para:")
    print(f"  Persona: {persona_numero}")
    print(f"  Cuenta: {gestion}/{internacion}/{cuenta_id}")
    print("="*80)

    # Obtener detalle completo
    detalle = client.get_detalle_atencion(
        persona_numero=persona_numero,
        cuenta_gestion=gestion,
        cuenta_internacion=internacion,
        cuenta_id=cuenta_id
    )

    if not detalle:
        print("❌ No se pudo obtener el detalle")
        return

    # Formatear para LLM (esto es lo que ve Claude)
    historial_formateado = formatear_atencion_para_llm(detalle)

    print("\n" + "="*80)
    print("HISTORIAL COMPLETO QUE SE ENVÍA A CLAUDE")
    print("="*80 + "\n")
    print(historial_formateado)
    print("\n" + "="*80)
    print("FIN DEL HISTORIAL")
    print("="*80)

    # Guardar en archivo para revisión detallada
    output_file = f"historial_raw_{gestion}_{internacion}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(historial_formateado)

    print(f"\n💾 Historial guardado en: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ver_historial_raw.py GESTION/INTERNACION")
        print("Ejemplo: python ver_historial_raw.py 2025/141671")
        sys.exit(1)

    cuenta = sys.argv[1]
    partes = cuenta.split('/')

    if len(partes) < 2:
        print("❌ Formato inválido. Use: GESTION/INTERNACION")
        sys.exit(1)

    gestion = int(partes[0])
    internacion = int(partes[1])

    ver_historial(gestion, internacion)

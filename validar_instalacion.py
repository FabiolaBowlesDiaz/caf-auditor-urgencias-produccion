"""
Script de Validación de Instalación
Sistema de Auditoría de Urgencias - Clínica Foianini

Ejecutar:
    python validar_instalacion.py

Este script verifica que todos los componentes del sistema estén
correctamente instalados y configurados para Urgencias.
"""

import ast
import os
import sys
from pathlib import Path

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)

def test_result(test_name, passed, message=""):
    """Print test result"""
    status = "[OK]" if passed else "[ERROR]"
    print(f"  {status} {test_name}")
    if message:
        print(f"      {message}")
    return passed

def main():
    print_section("VALIDACION DE INSTALACION - SISTEMA URGENCIAS")

    all_tests_passed = True

    # ============================================================
    # TEST 1: Estructura de Archivos
    # ============================================================
    print("\n[Fase 1] Verificando estructura de archivos...")

    required_files = [
        "main.py",
        "auditar_atencion.py",
        "generar_reporte.py",
        "ver_historial_raw.py",
        "queries/get_todas_atenciones_24h.sql",
        "queries/get_detalle_atencion.sql",
        "utils/__init__.py",
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        ".env.example",
        ".gitignore"
    ]

    for file_path in required_files:
        exists = Path(file_path).exists()
        all_tests_passed &= test_result(
            f"Archivo: {file_path}",
            exists,
            "FALTA" if not exists else ""
        )

    # ============================================================
    # TEST 2: Sintaxis de Python
    # ============================================================
    print("\n[Fase 2] Verificando sintaxis de Python...")

    python_files = ["main.py", "auditar_atencion.py", "generar_reporte.py", "ver_historial_raw.py"]

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            all_tests_passed &= test_result(f"Sintaxis: {py_file}", True)
        except SyntaxError as e:
            all_tests_passed &= test_result(
                f"Sintaxis: {py_file}",
                False,
                f"Error en linea {e.lineno}: {e.msg}"
            )

    # ============================================================
    # TEST 3: Modelo de Datos
    # ============================================================
    print("\n[Fase 3] Verificando modelo de datos...")

    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()

    all_tests_passed &= test_result(
        "Clase AuditoriaUrgenciaResultado",
        'class AuditoriaUrgenciaResultado' in main_content
    )

    all_tests_passed &= test_result(
        "Campo diagnostico_urgencia",
        'diagnostico_urgencia' in main_content
    )

    all_tests_passed &= test_result(
        "NO usa diagnostico_emergencia",
        'diagnostico_emergencia' not in main_content
    )

    # ============================================================
    # TEST 4: Prompt de Urgencias
    # ============================================================
    print("\n[Fase 4] Verificando prompt adaptado...")

    all_tests_passed &= test_result(
        "Contexto de urgencias presente",
        'CONTEXTO DE URGENCIAS' in main_content or 'urgencias' in main_content.lower()
    )

    all_tests_passed &= test_result(
        "Archivos de salida con prefijo urgencias",
        'auditoria_urgencias' in main_content
    )

    # ============================================================
    # TEST 5: Query SQL de Urgencias
    # ============================================================
    print("\n[Fase 5] Verificando query SQL principal...")

    with open('queries/get_todas_atenciones_24h.sql', 'r', encoding='utf-8') as f:
        query = f.read()

    all_tests_passed &= test_result(
        "Sector 50 (Urgencias)",
        'PacienteEvolucionSector = 50' in query
    )

    all_tests_passed &= test_result(
        "NO usa Sector 3 (Emergencias)",
        'PacienteEvolucionSector = 3' not in query
    )

    all_tests_passed &= test_result(
        "JOIN con tabla turno",
        'JOIN turno' in query
    )

    all_tests_passed &= test_result(
        "Filtro TurnoTipo = 'E'",
        "TurnoTipo = 'E'" in query
    )

    all_tests_passed &= test_result(
        "Ventana de 24 horas",
        'DATE_SUB(NOW(), INTERVAL 24 HOUR)' in query
    )

    # ============================================================
    # TEST 6: Scripts Auxiliares
    # ============================================================
    print("\n[Fase 6] Verificando scripts auxiliares...")

    with open('auditar_atencion.py', 'r', encoding='utf-8') as f:
        auditar_content = f.read()

    all_tests_passed &= test_result(
        "auditar_atencion.py importa AuditoriaUrgenciaResultado",
        'AuditoriaUrgenciaResultado' in auditar_content
    )

    all_tests_passed &= test_result(
        "auditar_atencion.py usa titulo Urgencias",
        'Servicio de Urgencias' in auditar_content
    )

    with open('generar_reporte.py', 'r', encoding='utf-8') as f:
        reporte_content = f.read()

    all_tests_passed &= test_result(
        "generar_reporte.py usa diagnostico_urgencia",
        'diagnostico_urgencia' in reporte_content
    )

    all_tests_passed &= test_result(
        "generar_reporte.py usa titulo Urgencias",
        'Servicio de Urgencias' in reporte_content
    )

    # ============================================================
    # TEST 7: Configuración
    # ============================================================
    print("\n[Fase 7] Verificando archivos de configuracion...")

    with open('pyproject.toml', 'r', encoding='utf-8') as f:
        pyproject = f.read()

    all_tests_passed &= test_result(
        "pyproject.toml usa nombre auditoria-urgencia",
        'auditoria-urgencia' in pyproject
    )

    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    all_tests_passed &= test_result(
        "README.md documenta sistema de Urgencias",
        'Urgencias' in readme and '50' in readme
    )

    # ============================================================
    # TEST 8: Carpetas de Output
    # ============================================================
    print("\n[Fase 8] Verificando estructura de carpetas...")

    all_tests_passed &= test_result(
        "Carpeta output/ existe",
        Path('output').is_dir()
    )

    all_tests_passed &= test_result(
        "Carpeta logs/ existe",
        Path('logs').is_dir()
    )

    all_tests_passed &= test_result(
        "Carpeta queries/ existe",
        Path('queries').is_dir()
    )

    all_tests_passed &= test_result(
        "Carpeta utils/ existe",
        Path('utils').is_dir()
    )

    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    print_section("RESUMEN DE VALIDACION")

    if all_tests_passed:
        print("\n[EXITO] Todos los tests pasaron correctamente!")
        print("\nEl sistema de Urgencias esta correctamente instalado y configurado.")
        print("\nProximos pasos:")
        print("  1. Copiar .env.example a .env y configurar credenciales")
        print("  2. Instalar dependencias: uv pip install .")
        print("  3. Probar auditoría individual: python auditar_atencion.py 2025/XXXXX")
        print("  4. Ejecutar auditoría diaria: python main.py")
        sys.exit(0)
    else:
        print("\n[ERROR] Algunos tests fallaron!")
        print("\nRevisa los mensajes de error arriba para identificar los problemas.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR CRITICO] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

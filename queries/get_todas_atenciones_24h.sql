-- Obtener TODAS las ATENCIONES ÚNICAS de urgencias de las últimas 24 horas
-- Para sistema de auditoría diaria de producción
-- IMPORTANTE: Agrupa por número de internación para evitar duplicados por múltiples evoluciones
-- FILTROS: Sector 50 (Urgencias) + TurnoTipo 'E' (Urgencias, excluye consultas 'P' y sobrecupo 'S')
-- No requiere parámetros: usa NOW() para calcular últimas 24 horas automáticamente

SELECT
    -- Tomamos la primera evolución como referencia (la más antigua de la atención)
    MIN(pe.EvolucionAutonumerico) AS id_evolucion,
    pe.PersonaNumero AS id_persona_paciente,
    MIN(pe.PacienteEvolucionFechaHora) AS fecha_atencion,  -- Fecha de la primera evolución (ingreso)

    -- MÉDICO QUE ATENDIÓ (tomamos el de la primera evolución)
    (SELECT u2.UsuarioPersonaCodigo
     FROM pacienteevolucion pe2
     JOIN usuario u2 ON u2.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
     WHERE pe2.PersonaNumero = pe.PersonaNumero
       AND pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
       AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
       AND pe2.PacienteEvolucionNroIntId = pe.PacienteEvolucionNroIntId
       AND pe2.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
     ORDER BY pe2.PacienteEvolucionFechaHora ASC
     LIMIT 1
    ) AS id_medico,

    (SELECT med2.PersonaNombreCompleto
     FROM pacienteevolucion pe2
     JOIN usuario u2 ON u2.UsuarioCodigo = pe2.PacienteEvolucionMUsuario
     JOIN persona med2 ON med2.PersonaNumero = u2.UsuarioPersonaCodigo
     WHERE pe2.PersonaNumero = pe.PersonaNumero
       AND pe2.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
       AND pe2.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
       AND pe2.PacienteEvolucionNroIntId = pe.PacienteEvolucionNroIntId
       AND pe2.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
     ORDER BY pe2.PacienteEvolucionFechaHora ASC
     LIMIT 1
    ) AS nombre_medico,

    -- CUENTA (para reporte HTML)
    pe.PacienteEvolucionGestion AS cuenta_gestion,
    pe.PacienteEvolucionNroInter AS cuenta_internacion,  -- Campo principal de agrupación
    pe.PacienteEvolucionNroIntId AS cuenta_id,           -- Campo secundario (para query detalle)

    -- PACIENTE (nombre completo para reporte HTML)
    pac.PersonaNombreCompleto AS nombre_paciente,
    pac.PersonaSexo AS sexo_paciente,
    pac.PersonaFechaNacimiento AS fecha_nacimiento_paciente,

    -- DIAGNÓSTICOS (de todas las evoluciones de esta atención)
    (
        SELECT GROUP_CONCAT(DISTINCT
            CONCAT(cie.CIE9CMCodigo, '-', cie.CIE9CMDescripcion)
            SEPARATOR ' | '
        )
        FROM pacienteevolucion pe3
        JOIN pacienteevoluciondiagnostico ped
            ON ped.PersonaNumero = pe3.PersonaNumero
            AND ped.PacienteEvolucionFechaHora = pe3.PacienteEvolucionFechaHora
        LEFT JOIN cie9cm cie ON cie.CIE9CMCodigo = ped.CIE9CMCodigo
        WHERE pe3.PersonaNumero = pe.PersonaNumero
          AND pe3.PacienteEvolucionGestion = pe.PacienteEvolucionGestion
          AND pe3.PacienteEvolucionNroInter = pe.PacienteEvolucionNroInter
          AND pe3.PacienteEvolucionNroIntId = pe.PacienteEvolucionNroIntId
          AND pe3.PacienteEvolucionBFecha = '1000-01-01 00:00:00'
    ) AS diagnosticos

FROM pacienteevolucion pe
JOIN persona pac
    ON pac.PersonaNumero = pe.PersonaNumero        -- Nombre del paciente
INNER JOIN turno t
    ON pe.TurnoNumero = t.TurnoNumero              -- JOIN con tabla turno para filtrar por tipo
WHERE pe.PacienteEvolucionSector = 50  -- Urgencias solamente (Sector 50)
  AND t.TurnoTipo = 'E'  -- Solo Urgencias ('E'), excluye Consulta ('P') y Sobrecupo ('S')
  AND pe.PacienteEvolucionFechaHora >= DATE_SUB(NOW(), INTERVAL 24 HOUR)  -- Últimas 24 horas
  AND pe.PacienteEvolucionBFecha = '1000-01-01 00:00:00'  -- No eliminados

-- AGRUPAR POR ATENCIÓN ÚNICA (cuenta completa)
GROUP BY
    pe.PersonaNumero,
    pe.PacienteEvolucionGestion,
    pe.PacienteEvolucionNroInter,
    pe.PacienteEvolucionNroIntId,
    pac.PersonaNombreCompleto,
    pac.PersonaSexo,
    pac.PersonaFechaNacimiento

ORDER BY MIN(pe.PacienteEvolucionFechaHora) DESC

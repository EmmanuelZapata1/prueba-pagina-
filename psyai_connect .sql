-- ============================================================
--  BASE DE DATOS: psyai_connect
--  Versión corregida y completa
--  Sincronizada con app.py, todos los archivos JS y HTML
-- ============================================================

DROP DATABASE IF EXISTS psyai_connect;
CREATE DATABASE psyai_connect
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE psyai_connect;

-- ============================================================
-- TABLA: Register
-- app.py usa el nombre de columna "contrasena" (sin tilde)
-- en TODOS sus queries: INSERT, SELECT, UPDATE
-- Se agrega "activo" que app.py usa en stats, bloqueo y roles
-- ============================================================
CREATE TABLE Register (
    idUsuario     INT AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(120) NOT NULL,
    email         VARCHAR(120) UNIQUE NOT NULL,
    contrasena    VARCHAR(200) NOT NULL,
    rol           ENUM('paciente','profesional','admin') NOT NULL,
    fotoPerfil    VARCHAR(255),
    estadoCuenta  ENUM('Activa','Suspendida') DEFAULT 'Activa',
    activo        TINYINT(1) NOT NULL DEFAULT 1,
    fechaRegistro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA: Login
-- app.py: INSERT INTO Login (idUsuario, email, contrasena)
-- ============================================================
CREATE TABLE Login (
    idLogin      INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario    INT NOT NULL,
    email        VARCHAR(120) NOT NULL,
    contrasena   VARCHAR(200) NOT NULL,
    ultimoAcceso DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idUsuario) REFERENCES Register(idUsuario)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLA: PerfilPaciente
-- app.py: SELECT edad, genero, numeroTelefonico
--         UPDATE edad, genero, numeroTelefonico
-- my.profile.html: editEdad, editGenero, editTelefono
-- ============================================================
CREATE TABLE PerfilPaciente (
    idPaciente          INT PRIMARY KEY,
    edad                INT,
    genero              VARCHAR(20),
    numeroTelefonico    VARCHAR(20),
    consentimientoDatos TINYINT(1) DEFAULT 0,
    FOREIGN KEY (idPaciente) REFERENCES Register(idUsuario)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLA: PerfilProfesional
-- app.py: SELECT especialidad, licencia, experiencia, estado
--         UPDATE especialidad, licencia, experiencia
-- my.profile2.html: editEspecialidad, editLicencia, editExperiencia
-- ============================================================
CREATE TABLE PerfilProfesional (
    idProfesional INT PRIMARY KEY,
    especialidad  VARCHAR(120),
    licencia      VARCHAR(120),
    experiencia   TEXT,
    estado        ENUM('Activo','Inactivo') DEFAULT 'Activo',
    FOREIGN KEY (idProfesional) REFERENCES Register(idUsuario)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLA: AuditoriaAccesos
-- app.py login: INSERT (idUsuario, accion, ip)
-- app.py /api/admin/logs: SELECT JOIN con Register
-- app.py /api/admin/ultimo-acceso: SELECT fecha ORDER BY DESC
-- ============================================================
CREATE TABLE AuditoriaAccesos (
    idAuditoria INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario   INT NOT NULL,
    accion      VARCHAR(100),
    ip          VARCHAR(50),
    fecha       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idUsuario) REFERENCES Register(idUsuario)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLA: Logs
-- No existía en el SQL original — app.py la usa constantemente
-- registrar_log(): INSERT (administrador, modulo, accion, detalle)
-- /api/admin/stats: SELECT COUNT logs hoy, SELECT ultimos 5
-- /api/admin/logs: SELECT idLog, administrador, modulo, accion, detalle, fecha
-- /api/admin/roles/historial: SELECT WHERE modulo = 'roles'
-- admin.logs.js: filtra por modulo = usuarios | roles | notificaciones | accesos
-- ============================================================
CREATE TABLE Logs (
    idLog         INT AUTO_INCREMENT PRIMARY KEY,
    administrador VARCHAR(120),
    modulo        VARCHAR(80),
    accion        VARCHAR(120),
    detalle       TEXT,
    fecha         DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA: Notificaciones
-- La tabla original solo tenía 5 columnas.
-- app.py INSERT usa: titulo, mensaje, tipo, destinatario,
--   email_individual, enviado_por, estado, fecha_programada
-- app.py SELECT devuelve: idNotificacion, titulo, mensaje, tipo,
--   destinatario, email_individual, enviado_por, estado, leido,
--   fecha, fecha_programada
-- admin.notifications.js: también usa fecha_envio (alias de fecha)
-- idUsuario es NULL porque notifs del admin no van a un usuario fijo
-- ============================================================
CREATE TABLE Notificaciones (
    idNotificacion   INT AUTO_INCREMENT PRIMARY KEY,
    idUsuario        INT NULL,
    titulo           VARCHAR(200),
    mensaje          TEXT,
    tipo             VARCHAR(50),
    destinatario     VARCHAR(80),
    email_individual VARCHAR(120),
    enviado_por      VARCHAR(120),
    estado           ENUM('enviado','pendiente') DEFAULT 'enviado',
    leido            TINYINT(1) DEFAULT 0,
    fecha            DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_programada DATETIME NULL,
    FOREIGN KEY (idUsuario) REFERENCES Register(idUsuario)
        ON DELETE SET NULL
);

-- ============================================================
-- TABLA: ConversacionesChatbot
-- chatbot.html: input name="mensaje"
-- trigger trg_alerta_emocional: nivelEmocionalDetectado = 'Alto'
-- ============================================================
CREATE TABLE ConversacionesChatbot (
    idConversacion           INT AUTO_INCREMENT PRIMARY KEY,
    idPaciente               INT NOT NULL,
    mensajeUsuario           TEXT,
    respuestaChatbot         TEXT,
    nivelEmocionalDetectado  VARCHAR(50),
    palabrasRiesgoDetectadas TEXT,
    fecha                    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idPaciente) REFERENCES Register(idUsuario)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLA: EvolucionPaciente
-- evolution.html: estado_emocional, nivel_energia, notas_personales
-- app.py SP: estadoEmocional, nivelEnergia, notasPersonales
-- ============================================================
CREATE TABLE EvolucionPaciente (
    idEvolucion        INT AUTO_INCREMENT PRIMARY KEY,
    idPaciente         INT NOT NULL,
    idConversacion     INT NULL,
    estadoEmocional    VARCHAR(100),
    nivelEnergia       INT,
    notasPersonales    TEXT,
    resultadoEmocional VARCHAR(100),
    fecha              DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idPaciente) REFERENCES Register(idUsuario)
        ON DELETE CASCADE,
    FOREIGN KEY (idConversacion) REFERENCES ConversacionesChatbot(idConversacion)
        ON DELETE SET NULL
);

-- ============================================================
-- TABLA: PacientesProfesional
-- patients.html: nombre, edad, sexo, contacto, direccion, notas,
--   sintomas, diagnostico, tratamiento, fecha_diagnostico
-- ============================================================
CREATE TABLE PacientesProfesional (
    idRegistro       INT AUTO_INCREMENT PRIMARY KEY,
    idProfesional    INT NOT NULL,
    idPaciente       INT NULL,
    nombre           VARCHAR(120),
    edad             INT,
    sexo             VARCHAR(20),
    contacto         VARCHAR(120),
    direccion        TEXT,
    notas            TEXT,
    sintomas         TEXT,
    diagnostico      TEXT,
    tratamiento      TEXT,
    fechaDiagnostico DATE,
    fecha            DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idProfesional) REFERENCES Register(idUsuario)
        ON DELETE CASCADE,
    FOREIGN KEY (idPaciente) REFERENCES Register(idUsuario)
        ON DELETE SET NULL
);

-- ============================================================
-- TABLA: Citas
-- agenda-quotes.html (paciente): tipoCita, date, time, motivo
-- my.agenda.html (profesional): paciente, fecha, hora, tipo_sesion, estado, notas
-- Se incluyen ambos campos: motivo (paciente) y notas (profesional)
-- ============================================================
CREATE TABLE Citas (
    idCita        INT AUTO_INCREMENT PRIMARY KEY,
    idPaciente    INT NOT NULL,
    idProfesional INT NOT NULL,
    fecha         DATE NOT NULL,
    hora          TIME NOT NULL,
    tipoCita      VARCHAR(80),
    tipoSesion    VARCHAR(80),
    motivo        TEXT,
    notas         TEXT,
    estado        ENUM('Pendiente','Completada','Cancelada') DEFAULT 'Pendiente',
    FOREIGN KEY (idPaciente)    REFERENCES Register(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idProfesional) REFERENCES Register(idUsuario) ON DELETE CASCADE
);

-- ============================================================
-- TABLA: Facturas
-- agenda-quotes.html: montoPagoModal, metodoPagoModal ('banco'|'tarjeta')
-- ============================================================
CREATE TABLE Facturas (
    idFactura     INT AUTO_INCREMENT PRIMARY KEY,
    idPaciente    INT NOT NULL,
    idProfesional INT NOT NULL,
    idCita        INT NULL,
    monto         DECIMAL(10,2),
    metodoPago    ENUM('banco','tarjeta') DEFAULT 'tarjeta',
    estadoPago    ENUM('Pendiente','Pagado') DEFAULT 'Pendiente',
    fecha         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idPaciente)    REFERENCES Register(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idProfesional) REFERENCES Register(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idCita)        REFERENCES Citas(idCita)       ON DELETE SET NULL
);

-- ============================================================
-- TABLA: ItemsFactura
-- modal de pago en agenda-quotes.html
-- ============================================================
CREATE TABLE ItemsFactura (
    idItem         INT AUTO_INCREMENT PRIMARY KEY,
    idFactura      INT NOT NULL,
    descripcion    VARCHAR(120),
    precioUnitario DECIMAL(10,2),
    FOREIGN KEY (idFactura) REFERENCES Facturas(idFactura) ON DELETE CASCADE
);

-- ============================================================
-- TABLA: Reportes
-- reports.html: paciente, fecha_inicio, fecha_fin, tipo_reporte
-- ============================================================
CREATE TABLE Reportes (
    idReporte     INT AUTO_INCREMENT PRIMARY KEY,
    idProfesional INT NOT NULL,
    idPaciente    INT NULL,
    tipoReporte   VARCHAR(80),
    fechaInicio   DATE,
    fechaFin      DATE,
    estado        ENUM('Pendiente','Completado') DEFAULT 'Pendiente',
    fecha         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idProfesional) REFERENCES Register(idUsuario) ON DELETE CASCADE,
    FOREIGN KEY (idPaciente)    REFERENCES Register(idUsuario) ON DELETE SET NULL
);


-- ============================================================
-- TRIGGERS
-- ============================================================

DELIMITER //

-- Notificar paciente cuando registra su evolución (evolution.html)
CREATE TRIGGER trg_evolucion_notificacion
AFTER INSERT ON EvolucionPaciente
FOR EACH ROW
BEGIN
    INSERT INTO Notificaciones (idUsuario, titulo, mensaje, tipo, estado, enviado_por)
    VALUES (NEW.idPaciente, 'Evolución registrada', 'Se ha registrado tu nueva evolución emocional.', 'Evolución', 'enviado', 'Sistema');
END //

-- Notificar al paciente cuando se agenda una cita
CREATE TRIGGER trg_cita_notificacion_paciente
AFTER INSERT ON Citas
FOR EACH ROW
BEGIN
    INSERT INTO Notificaciones (idUsuario, titulo, mensaje, tipo, estado, enviado_por)
    VALUES (NEW.idPaciente, 'Nueva cita', 'Se ha programado una nueva cita.', 'Cita', 'enviado', 'Sistema');
END //

-- Notificar al profesional cuando se agenda una cita
CREATE TRIGGER trg_cita_notificacion_profesional
AFTER INSERT ON Citas
FOR EACH ROW
BEGIN
    INSERT INTO Notificaciones (idUsuario, titulo, mensaje, tipo, estado, enviado_por)
    VALUES (NEW.idProfesional, 'Nueva cita agendada', 'Tienes una nueva cita agendada.', 'Cita', 'enviado', 'Sistema');
END //

-- Alerta si chatbot detecta nivel emocional Alto
CREATE TRIGGER trg_alerta_emocional
AFTER INSERT ON ConversacionesChatbot
FOR EACH ROW
BEGIN
    IF NEW.nivelEmocionalDetectado = 'Alto' THEN
        INSERT INTO Notificaciones (idUsuario, mensaje, tipo, estado)
        VALUES (
            NEW.idPaciente,
            'Se detectó un estado emocional crítico. Un profesional revisará tu caso.',
            'Alerta',
            'enviado'
        );
    END IF;
END //

-- Bloquear factura duplicada el mismo día para la misma cita
CREATE TRIGGER trg_evitar_factura_duplicada
BEFORE INSERT ON Facturas
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM Facturas
        WHERE idPaciente = NEW.idPaciente
          AND DATE(fecha) = CURDATE()
          AND idCita      = NEW.idCita
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Ya existe una factura para esta cita hoy.';
    END IF;
END //

-- Registrar en auditoría cuando se reactiva una cuenta suspendida
CREATE TRIGGER trg_registrar_reactivacion
AFTER UPDATE ON Register
FOR EACH ROW
BEGIN
    IF NEW.estadoCuenta = 'Activa' AND OLD.estadoCuenta = 'Suspendida' THEN
        INSERT INTO AuditoriaAccesos (idUsuario, accion, ip)
        VALUES (NEW.idUsuario, 'Reactivación de cuenta', '0.0.0.0');
    END IF;
END //

DELIMITER ;


-- ============================================================
-- PROCEDIMIENTOS ALMACENADOS
-- Prefijo sp_ para evitar conflicto con nombres de tablas
-- ============================================================

DELIMITER //

-- Registrar usuario nuevo
CREATE PROCEDURE sp_Register(
    IN p_nombre    VARCHAR(120),
    IN p_email     VARCHAR(120),
    IN p_contra    VARCHAR(200),
    IN p_rol       VARCHAR(20)
)
BEGIN
    INSERT INTO Register(nombre, email, contrasena, rol)
    VALUES (p_nombre, p_email, p_contra, p_rol);
END //

-- Autenticar usuario
CREATE PROCEDURE sp_Login(
    IN p_email  VARCHAR(120),
    IN p_contra VARCHAR(200)
)
BEGIN
    SELECT idUsuario, nombre, email, rol, estadoCuenta
    FROM Register
    WHERE email      = p_email
      AND contrasena = p_contra
      AND estadoCuenta = 'Activa';
END //

-- Agendar cita (paciente y profesional)
CREATE PROCEDURE sp_AgendarCita(
    IN p_paciente    INT,
    IN p_profesional INT,
    IN p_fecha       DATE,
    IN p_hora        TIME,
    IN p_tipoCita    VARCHAR(80),
    IN p_tipoSesion  VARCHAR(80),
    IN p_motivo      TEXT,
    IN p_notas       TEXT
)
BEGIN
    INSERT INTO Citas(idPaciente, idProfesional, fecha, hora, tipoCita, tipoSesion, motivo, notas)
    VALUES (p_paciente, p_profesional, p_fecha, p_hora, p_tipoCita, p_tipoSesion, p_motivo, p_notas);
END //

-- Crear factura tras pago
CREATE PROCEDURE sp_CrearFactura(
    IN p_paciente    INT,
    IN p_profesional INT,
    IN p_cita        INT,
    IN p_monto       DECIMAL(10,2),
    IN p_metodoPago  VARCHAR(20)
)
BEGIN
    INSERT INTO Facturas(idPaciente, idProfesional, idCita, monto, metodoPago)
    VALUES (p_paciente, p_profesional, p_cita, p_monto, p_metodoPago);
END //

-- Registrar evolución emocional del paciente
CREATE PROCEDURE sp_RegistrarEvolucion(
    IN p_paciente        INT,
    IN p_estadoEmocional VARCHAR(100),
    IN p_nivelEnergia    INT,
    IN p_notas           TEXT
)
BEGIN
    INSERT INTO EvolucionPaciente(idPaciente, estadoEmocional, nivelEnergia, notasPersonales)
    VALUES (p_paciente, p_estadoEmocional, p_nivelEnergia, p_notas);
END //

-- Generar reporte profesional
CREATE PROCEDURE sp_GenerarReporte(
    IN p_profesional INT,
    IN p_paciente    INT,
    IN p_tipo        VARCHAR(80),
    IN p_fechaInicio DATE,
    IN p_fechaFin    DATE
)
BEGIN
    INSERT INTO Reportes(idProfesional, idPaciente, tipoReporte, fechaInicio, fechaFin)
    VALUES (p_profesional, p_paciente, p_tipo, p_fechaInicio, p_fechaFin);
END //

DELIMITER ;


-- ============================================================
-- VISTAS
-- ============================================================

-- Citas pendientes — dashboards paciente y profesional
CREATE VIEW VistaCitasPendientes AS
SELECT
    c.idCita,
    u.nombre     AS paciente,
    c.fecha,
    c.hora,
    c.tipoCita,
    c.tipoSesion,
    c.motivo,
    c.notas,
    c.estado
FROM Citas c
JOIN Register u ON c.idPaciente = u.idUsuario
WHERE c.estado = 'Pendiente';

-- Historial del chatbot — chatbot.html
CREATE VIEW VistaHistorialChatbot AS
SELECT
    u.nombre,
    c.mensajeUsuario,
    c.respuestaChatbot,
    c.nivelEmocionalDetectado,
    c.fecha
FROM ConversacionesChatbot c
JOIN Register u ON c.idPaciente = u.idUsuario;

-- Evolución emocional — evolution.html
CREATE VIEW VistaEvolucionPaciente AS
SELECT
    u.nombre,
    e.estadoEmocional,
    e.nivelEnergia,
    e.notasPersonales,
    e.fecha
FROM EvolucionPaciente e
JOIN Register u ON e.idPaciente = u.idUsuario;

-- Facturación — agenda-quotes.html
CREATE VIEW VistaFacturacion AS
SELECT
    f.idFactura,
    u.nombre     AS paciente,
    f.monto,
    f.metodoPago,
    f.estadoPago,
    f.fecha
FROM Facturas f
JOIN Register u ON f.idPaciente = u.idUsuario;

-- Reportes del profesional — reports.html / patients.html
CREATE VIEW VistaReportes AS
SELECT
    r.idReporte,
    up.nombre    AS profesional,
    ua.nombre    AS paciente,
    r.tipoReporte,
    r.fechaInicio,
    r.fechaFin,
    r.estado,
    r.fecha
FROM Reportes r
JOIN  Register up ON r.idProfesional = up.idUsuario
LEFT JOIN Register ua ON r.idPaciente    = ua.idUsuario;

-- Logs combinados — replica la query de app.py /api/admin/logs
-- Une acciones de admin (tabla Logs) con logins (AuditoriaAccesos)
CREATE VIEW VistaLogsAdmin AS
SELECT
    l.idLog                                               AS id,
    l.administrador,
    l.modulo,
    l.accion,
    l.detalle,
    DATE_FORMAT(l.fecha, '%d/%m/%Y %H:%i')               AS fecha,
    'admin'                                               AS origen
FROM Logs l
UNION ALL
SELECT
    a.idAuditoria                                         AS id,
    COALESCE(r.nombre, CONCAT('Usuario #', a.idUsuario))  AS administrador,
    'accesos'                                             AS modulo,
    a.accion,
    CONCAT('IP: ', a.ip)                                  AS detalle,
    DATE_FORMAT(a.fecha, '%d/%m/%Y %H:%i')               AS fecha,
    'auditoria'                                           AS origen
FROM AuditoriaAccesos a
LEFT JOIN Register r ON a.idUsuario = r.idUsuario;


-- ============================================================
-- USUARIO ADMIN POR DEFECTO
-- app.py verifica admin con contraseña en texto plano
-- Cambiar la contraseña después del primer acceso
-- ============================================================
INSERT INTO Register (nombre, email, contrasena, rol, estadoCuenta, activo)
VALUES ('Administrador', 'admin@psyai.com', '60fe74406e7f353ed979f350f2fbb6a2e8690a5fa7d1b0c32983d1d8b3f95f67', 'admin', 'Activa', 1);

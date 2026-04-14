from flask import Flask, request, jsonify, session, send_from_directory, make_response
from flask_cors import CORS
import mysql.connector
import hashlib
import os
from datetime import datetime, timedelta, date

app = Flask(__name__, static_folder='.')
app._static_folder = '.'
app.secret_key = 'psyai_secret_key_2024'

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

CORS(app, supports_credentials=True, origins="*")

@app.route('/api/theme', methods=['GET', 'POST'])
def api_theme():
    if request.method == 'POST':
        theme = request.json.get('theme', 'light')
        resp = make_response(jsonify({'success': True}))
        resp.set_cookie('theme', theme, max_age=365*24*60*60, samesite='Lax')
        return resp
    else:
        theme = request.cookies.get('theme', 'light')
        is_dark = theme == 'dark'
        if is_dark:
            bg, fg = '#030610', '#daeeff'
        else:
            bg, fg = '#ffffff', '#212529'
        return jsonify({'theme': theme, 'dark': is_dark, 'bg': bg, 'fg': fg})

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'psyai_connect'
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SHOW COLUMNS FROM Reportes LIKE 'sintomas'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Reportes ADD COLUMN sintomas TEXT")
        
        cursor.execute("SHOW COLUMNS FROM Reportes LIKE 'diagnostico'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Reportes ADD COLUMN diagnostico TEXT")
        
        cursor.execute("SHOW COLUMNS FROM Reportes LIKE 'tratamiento'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Reportes ADD COLUMN tratamiento TEXT")
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error initializing DB:", e)

try:
    init_db()
except:
    pass

@app.route('/api/admin/crear-columnas-diagnostico', methods=['POST'])
def crear_columnas_diagnostico():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SHOW COLUMNS FROM Reportes LIKE 'sintomas'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Reportes ADD COLUMN sintomas TEXT")
        
        cursor.execute("SHOW COLUMNS FROM Reportes LIKE 'diagnostico'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Reportes ADD COLUMN diagnostico TEXT")
        
        cursor.execute("SHOW COLUMNS FROM Reportes LIKE 'tratamiento'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE Reportes ADD COLUMN tratamiento TEXT")
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Columnas creadas correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_log(cursor, modulo, accion, detalle, rol_anterior=None, rol_nuevo=None, usuario_afectado=None):
    try:
        cursor.execute("""
            INSERT INTO Logs (administrador, modulo, accion, detalle, rol_anterior, rol_nuevo, usuario_afectado)
            VALUES ('Admin', %s, %s, %s, %s, %s, %s)
        """, (modulo, accion, detalle, rol_anterior, rol_nuevo, usuario_afectado))
    except:
        pass


# ============================================================
# ARCHIVOS ESTATICOS
# ============================================================
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


# ============================================================
# REGISTRO
# ============================================================
@app.route('/api/register', methods=['POST'])
def register():
    data      = request.get_json()
    nombre    = data.get('nombre', '').strip()
    email     = data.get('email', '').strip()
    password  = data.get('password', '')
    confirmar = data.get('confirm_password', '')
    rol       = data.get('rol', 'paciente')
    genero    = data.get('genero', '')

    if not nombre or not email or not password:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
    if password != confirmar:
        return jsonify({'success': False, 'message': 'Las contrasenas no coinciden'}), 400
    if rol not in ('paciente', 'profesional'):
        return jsonify({'success': False, 'message': 'Rol invalido'}), 400

    hash_pass = hash_password(password)
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT idUsuario FROM Register WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'El correo ya esta registrado'}), 409
        cursor.execute(
            "INSERT INTO Register (nombre, email, contrasena, rol) VALUES (%s, %s, %s, %s)",
            (nombre, email, hash_pass, rol)
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
        if rol == 'paciente':
            cursor.execute(
                "INSERT INTO PerfilPaciente (idPaciente, genero) VALUES (%s, %s)",
                (nuevo_id, genero)
            )
        else:
            cursor.execute("INSERT INTO PerfilProfesional (idProfesional) VALUES (%s)", (nuevo_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Registro exitoso'}), 201
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# LOGIN
# ============================================================
@app.route('/api/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get('email', '').strip()
    password = data.get('password', '')
    rol      = data.get('rol', 'paciente')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email y contrasena requeridos'}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        if rol == 'admin':
            cursor.execute("""
                SELECT idUsuario, nombre, email, rol, estadoCuenta, fechaRegistro, fotoPerfil
                FROM Register
                WHERE email = %s AND contrasena = %s AND rol = 'admin' AND estadoCuenta = 'Activa'
            """, (email, password))
        else:
            hash_pass = hash_password(password)
            cursor.execute("""
                SELECT idUsuario, nombre, email, rol, estadoCuenta, fechaRegistro, fotoPerfil
                FROM Register
                WHERE email = %s AND contrasena = %s AND estadoCuenta = 'Activa'
            """, (email, hash_pass))

        usuario = cursor.fetchone()
        if not usuario:
            return jsonify({'success': False, 'message': 'Credenciales incorrectas o cuenta suspendida'}), 401
        if usuario['rol'] != rol:
            return jsonify({'success': False, 'message': f'Este usuario no tiene rol de {rol}'}), 403

        stored_pass = password if rol == 'admin' else hash_password(password)
        cursor.execute(
            "INSERT INTO Login (idUsuario, email, contrasena) VALUES (%s, %s, %s)",
            (usuario['idUsuario'], email, stored_pass)
        )
        cursor.execute(
            "INSERT INTO AuditoriaAccesos (idUsuario, accion, ip) VALUES (%s, %s, %s)",
            (usuario['idUsuario'], 'Login exitoso', request.remote_addr)
        )
        conn.commit()

        session['usuario'] = {
            'id':     usuario['idUsuario'],
            'nombre': usuario['nombre'],
            'email':  usuario['email'],
            'rol':    usuario['rol'],
            'fotoPerfil': usuario.get('fotoPerfil')
        }
        session['idUsuario'] = usuario['idUsuario']
        session['nombre']    = usuario['nombre']
        session['rol']       = usuario['rol']
        session['fotoPerfil'] = usuario.get('fotoPerfil')

        if usuario['rol'] == 'paciente':
            redirect_url = 'patient.dashboard.html'
        elif usuario['rol'] == 'profesional':
            redirect_url = 'professional.dashboard.html'
        else:
            redirect_url = 'admin.dashboard.html'

        return jsonify({
            'success':  True,
            'message':  'Login exitoso',
            'usuario':  session['usuario'],
            'idUsuario': session.get('idUsuario'),
            'nombre': session.get('nombre'),
            'rol': session.get('rol'),
            'redirect': redirect_url
        }), 200

    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# LOGOUT
# ============================================================
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Sesion cerrada'}), 200


# ============================================================
# SUBIR FOTO DE PERFIL
# ============================================================
@app.route('/api/usuario/foto', methods=['POST'])
def subir_foto_perfil():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'No se envió archivo'}), 400

    file = request.files['foto']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Archivo vacío'}), 400

    allowed = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return jsonify({'success': False, 'message': 'Tipo no permitido'}), 400

    idUsuario = session.get('idUsuario')
    filename = f"perfil_{idUsuario}_{int(datetime.now().timestamp())}.{ext}"
    upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Register SET fotoPerfil = %s WHERE idUsuario = %s", (filename, idUsuario))
        conn.commit()
        session['fotoPerfil'] = filename
        if 'usuario' in session and isinstance(session['usuario'], dict):
            session['usuario']['fotoPerfil'] = filename
        return jsonify({'success': True, 'message': 'Foto actualizada', 'foto': filename})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# SESION
# ============================================================
@app.route('/api/session', methods=['GET'])
def check_session():
    if 'usuario' in session:
        return jsonify({
            'success':   True,
            'logged_in': True,
            'usuario':   session['usuario'],
            'fotoPerfil': session.get('fotoPerfil')
        })
    return jsonify({'success': True, 'logged_in': False})


# ============================================================
# RECUPERAR CONTRASEÑA
# ============================================================
@app.route('/api/recover', methods=['POST'])
def recover_password():
    data  = request.get_json()
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'message': 'Email requerido'}), 400
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT idUsuario FROM Register WHERE email = %s AND estadoCuenta = 'Activa'",
            (email,)
        )
        cursor.fetchone()
        return jsonify({'success': True, 'message': 'Si el correo existe, recibiras instrucciones.'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# PERFIL PACIENTE
# ============================================================
@app.route('/api/perfil/paciente/<int:id_usuario>', methods=['GET'])
def get_perfil_paciente(id_usuario):
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.nombre, r.email, r.fotoPerfil, r.fechaRegistro,
                   p.edad, p.genero, p.numeroTelefonico
            FROM Register r
            LEFT JOIN PerfilPaciente p ON r.idUsuario = p.idPaciente
            WHERE r.idUsuario = %s
        """, (id_usuario,))
        perfil = cursor.fetchone()
        if not perfil:
            return jsonify({'success': False, 'message': 'Perfil no encontrado'}), 404
        if perfil.get('fechaRegistro'):
            perfil['fechaRegistro'] = perfil['fechaRegistro'].strftime('%d/%m/%Y')
        return jsonify({'success': True, 'perfil': perfil})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/perfil/paciente/editar', methods=['POST'])
def editar_perfil_paciente():
    data = request.get_json()
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE PerfilPaciente
            SET edad = %s, genero = %s, numeroTelefonico = %s
            WHERE idPaciente = %s
        """, (data.get('edad'), data.get('genero'), data.get('numeroTelefonico'), data.get('idUsuario')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Perfil actualizado'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# PERFIL PROFESIONAL
# ============================================================
@app.route('/api/perfil/profesional/<int:id_usuario>', methods=['GET'])
def get_perfil_profesional(id_usuario):
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.nombre, r.email, r.fotoPerfil, r.fechaRegistro,
                   p.especialidad, p.licencia, p.experiencia, p.estado
            FROM Register r
            LEFT JOIN PerfilProfesional p ON r.idUsuario = p.idProfesional
            WHERE r.idUsuario = %s
        """, (id_usuario,))
        perfil = cursor.fetchone()
        if not perfil:
            return jsonify({'success': False, 'message': 'Perfil no encontrado'}), 404
        if perfil.get('fechaRegistro'):
            perfil['fechaRegistro'] = perfil['fechaRegistro'].strftime('%d/%m/%Y')
        return jsonify({'success': True, 'perfil': perfil})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/perfil/profesional/editar', methods=['POST'])
def editar_perfil_profesional():
    data = request.get_json()
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE PerfilProfesional
            SET especialidad = %s, licencia = %s, experiencia = %s
            WHERE idProfesional = %s
        """, (data.get('especialidad'), data.get('licencia'), data.get('experiencia'), data.get('idUsuario')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Perfil actualizado'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# DISPONIBILIDAD (PROFESIONAL)
# ============================================================
@app.route('/api/disponibilidad/crear', methods=['POST'])
def crear_disponibilidad():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data           = request.get_json()
    id_profesional = session.get('idUsuario')
    fecha          = data.get('fecha')
    hora_inicio    = data.get('hora_inicio')
    hora_fin       = data.get('hora_fin')
    if not fecha or not hora_inicio or not hora_fin:
        return jsonify({'success': False, 'message': 'Datos incompletos'})

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Disponibilidad (idProfesional, fecha, hora_inicio, hora_fin, estado)
            VALUES (%s, %s, %s, %s, 'Disponible')
        """, (id_profesional, fecha, hora_inicio, hora_fin))
        conn.commit()
        return jsonify({'success': True, 'message': 'Disponibilidad agregada'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/disponibilidad/<int:id_profesional>', methods=['GET'])
def ver_disponibilidad(id_profesional):
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT fecha, hora_inicio, hora_fin, estado
            FROM Disponibilidad
            WHERE idProfesional = %s AND estado = 'Disponible'
        """, (id_profesional,))
        
        datos = cursor.fetchall()
        
        for d in datos:
            if hasattr(d['hora_inicio'], '__str__'):
                d['hora_inicio'] = str(d['hora_inicio'])
            if hasattr(d['hora_fin'], '__str__'):
                d['hora_fin'] = str(d['hora_fin'])
            if hasattr(d['fecha'], 'isoformat'):
                d['fecha'] = d['fecha'].isoformat()
        
        return jsonify({'success': True, 'disponibilidad': datos})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# ADMIN - STATS
# ============================================================
@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) as total FROM Register WHERE rol != 'admin'")
        total = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as activos FROM Register WHERE rol != 'admin' AND COALESCE(activo,1) = 1 AND estadoCuenta = 'Activa'")
        activos = cursor.fetchone()['activos']

        cursor.execute("SELECT COUNT(*) as bloqueados FROM Register WHERE rol != 'admin' AND (activo = 0 OR estadoCuenta = 'Suspendida')")
        bloqueados = cursor.fetchone()['bloqueados']

        cursor.execute("SELECT COUNT(*) as notifs FROM Notificaciones")
        notifs = cursor.fetchone()['notifs']

        cursor.execute("SELECT COUNT(*) as logs_hoy FROM Logs WHERE DATE(fecha) = CURDATE()")
        logs_hoy = cursor.fetchone()['logs_hoy']

        cursor.execute("SELECT accion, detalle, DATE_FORMAT(fecha,'%d/%m/%Y %H:%i') as fecha FROM Logs ORDER BY fecha DESC LIMIT 5")
        actividad = cursor.fetchall()

        return jsonify({'success': True, 'stats': {
            'total_usuarios':     total,
            'usuarios_activos':   activos,
            'cuentas_suspendidas': bloqueados,
            'notificaciones':     notifs,
            'logs_hoy':           logs_hoy,
            'actividad_reciente': actividad
        }})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# ADMIN - USUARIOS
# ============================================================
@app.route('/api/admin/usuarios', methods=['GET'])
def get_usuarios():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.idUsuario, r.nombre, r.email, r.rol,
                   COALESCE(r.activo, 1) as activo,
                   r.estadoCuenta,
                   DATE_FORMAT(r.fechaRegistro, '%d/%m/%Y') as fechaRegistro,
                   (SELECT DATE_FORMAT(MAX(a.fecha),'%d/%m/%Y %H:%i')
                    FROM AuditoriaAccesos a WHERE a.idUsuario = r.idUsuario) as ultimoAcceso
            FROM Register r
            WHERE r.rol != 'admin'
            ORDER BY r.fechaRegistro DESC
        """)
        usuarios = cursor.fetchall()
        return jsonify({'success': True, 'usuarios': usuarios})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/admin/usuarios/<int:id_usuario>', methods=['GET'])
def get_usuario(id_usuario):
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT idUsuario, nombre, email, rol,
                   COALESCE(activo,1) as activo, estadoCuenta,
                   DATE_FORMAT(fechaRegistro,'%d/%m/%Y') as fechaRegistro
            FROM Register WHERE idUsuario = %s
        """, (id_usuario,))
        usuario = cursor.fetchone()
        if not usuario:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        return jsonify({'success': True, 'usuario': usuario})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/admin/usuarios/crear', methods=['POST'])
def crear_usuario():
    data = request.get_json()
    try:
        conn      = get_connection()
        cursor    = conn.cursor()
        hash_pass = hash_password(data.get('contrasena', '1234'))
        cursor.execute("""
            INSERT INTO Register (nombre, email, contrasena, rol)
            VALUES (%s, %s, %s, %s)
        """, (data.get('nombre'), data.get('email'), hash_pass, data.get('rol', 'paciente')))
        conn.commit()
        nuevo_id = cursor.lastrowid
        if data.get('rol') == 'paciente':
            cursor.execute("INSERT INTO PerfilPaciente (idPaciente) VALUES (%s)", (nuevo_id,))
        elif data.get('rol') == 'profesional':
            cursor.execute("INSERT INTO PerfilProfesional (idProfesional) VALUES (%s)", (nuevo_id,))
        conn.commit()
        registrar_log(cursor, 'usuarios', 'Crear usuario', f"Usuario creado: {data.get('nombre')} - Rol: {data.get('rol')}")
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario creado correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/admin/usuarios/editar', methods=['POST'])
def editar_usuario():
    data = request.get_json()
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Register SET nombre = %s, email = %s, estadoCuenta = %s
            WHERE idUsuario = %s
        """, (data.get('nombre'), data.get('email'), data.get('estado'), data.get('idUsuario')))
        conn.commit()
        registrar_log(cursor, 'usuarios', 'Editar usuario', f"Usuario editado: {data.get('nombre')}")
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario actualizado'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/admin/usuarios/eliminar', methods=['POST'])
def eliminar_usuario():
    data = request.get_json()
    try:
        conn    = get_connection()
        cursor  = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM Register WHERE idUsuario = %s", (data.get('idUsuario'),))
        u       = cursor.fetchone()
        cursor2 = conn.cursor()
        cursor2.execute("DELETE FROM Register WHERE idUsuario = %s", (data.get('idUsuario'),))
        conn.commit()
        registrar_log(cursor2, 'usuarios', 'Eliminar usuario', f"Usuario eliminado: {u['nombre'] if u else data.get('idUsuario')}")
        conn.commit()
        return jsonify({'success': True, 'message': 'Usuario eliminado'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: conn.close()
        except: pass


@app.route('/api/admin/usuarios/bloquear', methods=['POST'])
def bloquear_usuario():
    data   = request.get_json()
    accion = data.get('accion')
    activo = 0 if accion in ('bloquear', 'suspender') else 1
    estado = 'Suspendida' if activo == 0 else 'Activa'
    try:
        conn    = get_connection()
        cursor  = conn.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM Register WHERE idUsuario = %s", (data.get('idUsuario'),))
        u       = cursor.fetchone()
        cursor2 = conn.cursor()
        cursor2.execute("""
            UPDATE Register SET activo = %s, estadoCuenta = %s WHERE idUsuario = %s
        """, (activo, estado, data.get('idUsuario')))
        conn.commit()
        accion_str = 'Suspender usuario' if activo == 0 else 'Reestablecer usuario'
        registrar_log(cursor2, 'usuarios', accion_str, f"{'Suspendido' if activo==0 else 'Reestablecido'}: {u['nombre'] if u else ''}")
        conn.commit()
        return jsonify({'success': True, 'message': f"Usuario {'suspendido' if activo==0 else 'reestablecido'}"})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: conn.close()
        except: pass


# ============================================================
# ADMIN - ROLES
# ============================================================
@app.route('/api/admin/roles/usuarios', methods=['GET'])
def get_usuarios_roles():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT idUsuario, nombre, email, rol,
                   COALESCE(activo,1) as activo,
                   DATE_FORMAT(fechaRegistro,'%d/%m/%Y') as fechaRegistro
            FROM Register WHERE rol != 'admin' ORDER BY nombre
        """)
        usuarios = cursor.fetchall()
        return jsonify({'success': True, 'usuarios': usuarios})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/admin/roles/cambiar', methods=['POST'])
def cambiar_rol():
    data = request.get_json()
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT nombre, rol FROM Register WHERE idUsuario = %s", (data.get('idUsuario'),))
        u            = cursor.fetchone()
        rol_anterior = u['rol'] if u else '-'
        
        cursor2 = conn.cursor()
        cursor2.execute("UPDATE Register SET rol = %s WHERE idUsuario = %s", (data.get('nuevoRol'), data.get('idUsuario')))
        conn.commit()
        
        try:
            cursor2.execute("ALTER TABLE Logs ADD COLUMN rol_anterior VARCHAR(20) DEFAULT NULL")
            cursor2.execute("ALTER TABLE Logs ADD COLUMN rol_nuevo VARCHAR(20) DEFAULT NULL")
            cursor2.execute("ALTER TABLE Logs ADD COLUMN usuario_afectado VARCHAR(100) DEFAULT NULL")
            conn.commit()
        except:
            pass
        
        registrar_log(cursor2, 'roles', 'Cambio de rol', f"{u['nombre'] if u else ''}: {rol_anterior} -> {data.get('nuevoRol')}", rol_anterior, data.get('nuevoRol'), u['nombre'] if u else None)
        conn.commit()
        return jsonify({'success': True, 'message': 'Rol actualizado'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: conn.close()
        except: pass


@app.route('/api/admin/roles/historial', methods=['GET'])
def get_historial_roles():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM Logs WHERE modulo = 'roles'
            ORDER BY fecha DESC LIMIT 50
        """)
        historial = cursor.fetchall()
        for h in historial:
            if h.get('fecha'):
                h['fecha'] = h['fecha'].strftime('%d/%m/%Y %H:%M')
        return jsonify({'success': True, 'historial': historial})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# ADMIN - NOTIFICACIONES
# ============================================================
# ADMIN - NOTIFICACIONES Y ACTIVIDADES
# ============================================================
@app.route('/api/admin/notificaciones', methods=['GET'])
def get_notificaciones():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Notificaciones enviadas por el admin
        cursor.execute("""
            SELECT idNotificacion, titulo, mensaje, tipo,
                   destinatario, email_individual, enviado_por,
                   estado, leido,
                   DATE_FORMAT(fecha,'%d/%m/%Y %H:%i') as fecha,
                   DATE_FORMAT(fecha,'%d/%m/%Y %H:%i') as fecha_envio,
                   fecha_programada,
                   'notificacion' as tipo_registro
            FROM notificaciones
            ORDER BY fecha DESC LIMIT 100
        """)
        notifs = cursor.fetchall()
        
        # Actividades de profesionales (citas creadas, diagnósticos, etc)
        cursor.execute("""
            SELECT 
                CONCAT('Cita: ', c.tipoCita) as titulo,
                CONCAT('Paciente: ', r.nombre) as mensaje,
                'profesional' as tipo,
                'enviado' as estado,
                r.nombre as enviado_por,
                DATE_FORMAT(c.fecha,'%d/%m/%Y %H:%i') as fecha,
                'profesional' as tipo_registro
            FROM Citas c
            JOIN Register r ON c.idProfesional = r.idUsuario
            ORDER BY c.fecha DESC LIMIT 50
        """)
        actividades_prof = cursor.fetchall()
        
        # Actividades de pacientes (citas solicitadas)
        cursor.execute("""
            SELECT 
                CONCAT('Cita solicitada por: ', r.nombre) as titulo,
                CONCAT('Profesional: ', p.nombre) as mensaje,
                'paciente' as tipo,
                'enviado' as estado,
                r.nombre as enviado_por,
                DATE_FORMAT(c.fecha,'%d/%m/%Y %H:%i') as fecha,
                'paciente' as tipo_registro
            FROM Citas c
            JOIN Register r ON c.idPaciente = r.idUsuario
            JOIN Register p ON c.idProfesional = p.idUsuario
            ORDER BY c.fecha DESC LIMIT 50
        """)
        actividades_pac = cursor.fetchall()
        
        # Combinar todas las actividades
        todas_actividades = notifs + actividades_prof + actividades_pac
        todas_actividades.sort(key=lambda x: x['fecha'], reverse=True)
        
        total = len(todas_actividades)
        # Enviadas = todo lo que no sea pendiente (igual que el frontend)
        notificaciones_enviadas = sum(1 for n in todas_actividades if n.get('estado') != 'pendiente')
        programadas = sum(1 for n in todas_actividades if n.get('estado') == 'pendiente')
        
        return jsonify({
            'success': True,
            'notificaciones': todas_actividades[:100],
            'stats': {
                'enviadas': notificaciones_enviadas,
                'programadas': programadas,
                'tasa': f"{round((notificaciones_enviadas/total)*100)}%" if total else "0%",
                'alcanzados': total
            }
        })
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/admin/notificaciones/crear', methods=['POST'])
def crear_notificacion():
    data   = request.get_json()
    estado = 'enviado' if data.get('envio') == 'inmediato' else 'pendiente'
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Notificaciones
                (titulo, mensaje, tipo, destinatario, email_individual, enviado_por, estado, fecha_programada)
            VALUES (%s, %s, %s, %s, %s, 'Admin', %s, %s)
        """, (
            data.get('titulo'),
            data.get('mensaje'),
            data.get('tipo', 'info'),
            data.get('destinatario'),
            data.get('email_individual'),
            estado,
            data.get('fecha_programada') or None
        ))
        conn.commit()
        registrar_log(cursor, 'notificaciones', 'Enviar notificacion', f"{data.get('titulo')} -> {data.get('destinatario')}")
        conn.commit()
        return jsonify({'success': True, 'message': 'Notificacion enviada'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


@app.route('/api/admin/notificaciones/eliminar', methods=['POST'])
def eliminar_notificacion():
    data = request.get_json()
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Notificaciones WHERE idNotificacion = %s", (data.get('idNotificacion'),))
        conn.commit()
        registrar_log(cursor, 'notificaciones', 'Eliminar notificacion', f"ID: {data.get('idNotificacion')}")
        conn.commit()
        return jsonify({'success': True, 'message': 'Notificacion eliminada'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# ADMIN - LOGS (INCLUYE NOTIFICACIONES Y ACTIVIDADES)
# ============================================================
@app.route('/api/admin/logs', methods=['GET'])
def get_logs():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Logs del admin
        cursor.execute("""
            SELECT idLog as id, administrador, modulo, accion, detalle,
                   DATE_FORMAT(fecha,'%d/%m/%Y %H:%i') as fecha,
                   'admin' as origen
            FROM logs ORDER BY fecha DESC LIMIT 200
        """)
        logs_admin = cursor.fetchall()

        # Logs de accesos (login)
        cursor.execute("""
            SELECT a.idAuditoria as id,
                   COALESCE(r.nombre, CONCAT('Usuario #', a.idUsuario)) as administrador,
                   'accesos' as modulo,
                   a.accion,
                   CONCAT('IP: ', a.ip) as detalle,
                   DATE_FORMAT(a.fecha,'%d/%m/%Y %H:%i') as fecha,
                   'auditoria' as origen
            FROM auditoriaaccesos a
            LEFT JOIN register r ON a.idUsuario = r.idUsuario
            ORDER BY a.fecha DESC LIMIT 200
        """)
        logs_auditoria = cursor.fetchall()

        # Notificaciones del admin
        cursor.execute("""
            SELECT idNotificacion as id,
                   enviado_por as administrador,
                   'notificaciones' as modulo,
                   CONCAT('Notificación: ', titulo) as accion,
                   CONCAT(destinatario, ' - ', mensaje) as detalle,
                   DATE_FORMAT(fecha,'%d/%m/%Y %H:%i') as fecha,
                   'notificacion' as origen
            FROM notificaciones
            ORDER BY fecha DESC LIMIT 100
        """)
        logs_notificaciones = cursor.fetchall()

        # Actividades de profesionales (citas, diagnósticos)
        cursor.execute("""
            SELECT 
                c.idCita as id,
                pr.nombre as administrador,
                'notificaciones' as modulo,
                CONCAT('Cita profesional: ', c.tipoCita) as accion,
                CONCAT('Paciente: ', pa.nombre, ' - Fecha: ', DATE_FORMAT(c.fecha,'%d/%m/%Y')) as detalle,
                DATE_FORMAT(c.fecha,'%d/%m/%Y %H:%i') as fecha,
                'profesional' as origen
            FROM Citas c
            JOIN Register pr ON c.idProfesional = pr.idUsuario
            JOIN Register pa ON c.idPaciente = pa.idUsuario
            ORDER BY c.fecha DESC LIMIT 100
        """)
        logs_profesionales = cursor.fetchall()

        # Actividades de pacientes (citas solicitadas)
        cursor.execute("""
            SELECT 
                c.idCita as id,
                pa.nombre as administrador,
                'notificaciones' as modulo,
                CONCAT('Cita paciente: ', c.tipoCita) as accion,
                CONCAT('Profesional: ', pr.nombre, ' - Fecha: ', DATE_FORMAT(c.fecha,'%d/%m/%Y')) as detalle,
                DATE_FORMAT(c.fecha,'%d/%m/%Y %H:%i') as fecha,
                'paciente' as origen
            FROM Citas c
            JOIN Register pa ON c.idPaciente = pa.idUsuario
            JOIN Register pr ON c.idProfesional = pr.idUsuario
            ORDER BY c.fecha DESC LIMIT 100
        """)
        logs_pacientes = cursor.fetchall()

        # Combinar todos
        todos = logs_admin + logs_auditoria + logs_notificaciones + logs_profesionales + logs_pacientes
        todos.sort(key=lambda x: x['fecha'], reverse=True)

        return jsonify({'success': True, 'logs': todos})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - CREAR
# ============================================================
@app.route('/api/citas/crear', methods=['POST'])
def crear_cita():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data          = request.get_json()
    idPaciente    = session['idUsuario']
    idProfesional = data.get('idProfesional')
    fecha         = data.get('fecha')
    hora          = data.get('hora')
    tipoCita      = data.get('tipoCita')
    motivo        = data.get('motivo')

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idCita FROM Citas
            WHERE idProfesional = %s AND fecha = %s AND hora = %s
            AND estado != 'Cancelada'
        """, (idProfesional, fecha, hora))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Horario no disponible'})
        cursor.execute("""
            INSERT INTO Citas (idPaciente, idProfesional, fecha, hora, tipoCita, motivo, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente')
        """, (idPaciente, idProfesional, fecha, hora, tipoCita, motivo))
        conn.commit()
        return jsonify({'success': True, 'message': 'Cita agendada correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - HORARIOS DISPONIBLES
# ============================================================
@app.route('/api/citas/disponibles', methods=['POST'])
def horarios_disponibles():
    data          = request.get_json()
    idProfesional = data.get('idProfesional')
    fecha         = data.get('fecha')

    if not idProfesional or not fecha:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT hora_inicio, hora_fin
            FROM Disponibilidad
            WHERE idProfesional = %s AND DATE(fecha) = %s AND estado = 'Disponible'
        """, (idProfesional, fecha))
        disponibilidad = cursor.fetchone()
        
        if not disponibilidad:
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'horarios': []})

        inicio = disponibilidad['hora_inicio']
        fin    = disponibilidad['hora_fin']
        
        if isinstance(inicio, timedelta):
            inicio = (datetime.min + inicio).time()
        if isinstance(fin, timedelta):
            fin = (datetime.min + fin).time()

        cursor.execute("""
            SELECT hora FROM Citas
            WHERE idProfesional = %s AND fecha = %s AND estado != 'Cancelada'
        """, (idProfesional, fecha))
        ocupadas    = [str(row['hora']) for row in cursor.fetchall()]
        
        horarios    = []
        hora_actual = inicio
        while hora_actual < fin:
            h_str = str(hora_actual)
            if h_str not in ocupadas:
                horarios.append(h_str)
            dt_actual   = datetime.combine(date.today(), hora_actual)
            hora_actual = (dt_actual + timedelta(minutes=30)).time()
        
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'horarios': horarios})
    except Exception as e:
        print(f"Error en horarios_disponibles: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
        try: conn.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - CREAR POR PROFESIONAL
# ============================================================
@app.route('/api/citas/crear-profesional', methods=['POST'])
def crear_cita_profesional():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data          = request.get_json()
    idPaciente    = data.get('idPaciente')
    idProfesional = data.get('idProfesional')
    fecha         = data.get('fecha')
    hora          = data.get('hora')
    tipoCita      = data.get('tipoCita')
    motivo        = data.get('motivo')

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idCita FROM Citas
            WHERE idProfesional = %s AND fecha = %s AND hora = %s
            AND estado != 'Cancelada'
        """, (idProfesional, fecha, hora))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Ese horario ya está ocupado'})
        cursor.execute("""
            INSERT INTO Citas (idPaciente, idProfesional, fecha, hora, tipoCita, motivo, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente')
        """, (idPaciente, idProfesional, fecha, hora, tipoCita, motivo))
        conn.commit()
        return jsonify({'success': True, 'message': 'Cita agendada correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# PACIENTES - LISTAR
# ============================================================
@app.route('/api/pacientes/listar', methods=['GET'])
def listar_pacientes():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT idUsuario, nombre FROM Register
            WHERE rol = 'paciente'
            ORDER BY nombre
        """)
        pacientes = cursor.fetchall()
        return jsonify({'success': True, 'pacientes': pacientes})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# PROFESIONALES - LISTAR
# ============================================================
@app.route('/api/profesionales/listar', methods=['GET'])
def listar_profesionales():
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT idUsuario, nombre FROM Register
            WHERE rol = 'profesional'
            ORDER BY nombre
        """)
        profesionales = cursor.fetchall()
        return jsonify({'success': True, 'profesionales': profesionales})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - LISTAR POR PROFESIONAL
# ============================================================
@app.route('/api/citas/profesional', methods=['GET'])
def citas_profesional():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idProfesional = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.idCita, r.nombre as paciente, r.fotoPerfil, c.fecha, c.hora,
                   c.tipoCita, c.motivo, c.estado
            FROM Citas c
            JOIN Register r ON c.idPaciente = r.idUsuario
            WHERE c.idProfesional = %s AND c.estado != 'Cancelada'
            ORDER BY c.fecha ASC, c.hora ASC
        """, (idProfesional,))
        citas = cursor.fetchall()
        for c in citas:
            if c.get('fecha'): c['fecha'] = c['fecha'].strftime('%d/%m/%Y')
            if c.get('hora'):  c['hora']  = str(c['hora'])
            if c.get('fotoPerfil'): c['foto_perfil'] = c['fotoPerfil']
        return jsonify({'success': True, 'citas': citas})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - HORARIOS OCUPADOS DEL PROFESIONAL
# ============================================================
@app.route('/api/citas/profesional/horarios', methods=['POST'])
def horarios_ocupados_profesional():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data = request.get_json()
    idProfesional = data.get('idProfesional')
    fecha = data.get('fecha')

    if not idProfesional or not fecha:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hora FROM Citas
            WHERE idProfesional = %s AND fecha = %s AND estado != 'Cancelada'
        """, (idProfesional, fecha))
        horas_ocupadas = [str(row[0]) for row in cursor.fetchall()]
        return jsonify({'success': True, 'horarios_ocupados': horas_ocupadas})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - PRÓXIMA CITA PACIENTE
# ============================================================
@app.route('/api/citas/proxima', methods=['GET'])
def proxima_cita_paciente():
    if 'usuario' not in session:
        return jsonify({'success': True, 'cita': None})

    idPaciente = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.fecha, c.hora, c.tipoCita, r.nombre as profesional
            FROM Citas c
            JOIN Register r ON c.idProfesional = r.idUsuario
            WHERE c.idPaciente = %s AND c.estado = 'Pendiente' AND c.fecha >= CURDATE()
            ORDER BY c.fecha ASC, c.hora ASC LIMIT 1
        """, (idPaciente,))
        cita = cursor.fetchone()
        if not cita:
            return jsonify({'success': True, 'cita': None})
        cita['fecha'] = cita['fecha'].strftime('%d/%m/%Y')
        cita['hora']  = str(cita['hora'])
        return jsonify({'success': True, 'cita': cita})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - SOLICITADAS (PENDIENTES) POR PROFESIONAL
# ============================================================
@app.route('/api/citas/solicitadas', methods=['GET'])
def citas_solicitadas():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idProfesional = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.idCita, r.nombre as paciente, r.fotoPerfil, c.fecha, c.hora,
                   c.tipoCita, c.motivo, c.estado
            FROM Citas c
            JOIN Register r ON c.idPaciente = r.idUsuario
            WHERE c.idProfesional = %s AND c.estado = 'Pendiente'
            ORDER BY c.fecha ASC, c.hora ASC
        """, (idProfesional,))
        citas = cursor.fetchall()
        for c in citas:
            if c.get('fecha'): c['fecha'] = c['fecha'].strftime('%d/%m/%Y')
            if c.get('hora'):  c['hora']  = str(c['hora'])
        return jsonify({'success': True, 'citas': citas})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - ACTUALIZAR ESTADO (ACEPTAR/RECHAZAR)
# ============================================================
@app.route('/api/citas/actualizar-estado', methods=['POST'])
def actualizar_estado_cita():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data = request.get_json()
    idCita = data.get('idCita')
    estado = data.get('estado')

    if not idCita or not estado:
        return jsonify({'success': False, 'message': 'Datos incompletos'}), 400

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT idProfesional FROM Citas WHERE idCita = %s", (idCita,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Cita no encontrada'}), 404
        
        idProfesional = row[0]
        if idProfesional != session.get('idUsuario'):
            return jsonify({'success': False, 'message': 'No tienes permiso'}), 403
        
        cursor.execute("UPDATE Citas SET estado = %s WHERE idCita = %s", (estado, idCita))
        conn.commit()
        return jsonify({'success': True, 'message': f'Cita {estado}'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - LISTAR POR PACIENTE (HISTORIAL COMPLETO)
# ============================================================
@app.route('/api/citas/paciente', methods=['GET'])
def citas_paciente():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idPaciente = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.idCita, c.fecha, c.hora, c.tipoCita, c.motivo, c.estado,
                   r.nombre as profesional
            FROM Citas c
            JOIN Register r ON c.idProfesional = r.idUsuario
            WHERE c.idPaciente = %s AND c.estado != 'Cancelada'
            ORDER BY c.fecha ASC, c.hora ASC
        """, (idPaciente,))
        citas = cursor.fetchall()
        for c in citas:
            if c.get('fecha'): c['fecha'] = c['fecha'].strftime('%d/%m/%Y')
            if c.get('hora'):  c['hora']  = str(c['hora'])
        return jsonify({'success': True, 'citas': citas})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# CITAS - CANCELAR
# ============================================================
@app.route('/api/citas/cancelar', methods=['POST'])
def cancelar_cita():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data   = request.get_json()
    idCita = data.get('idCita')
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Citas SET estado = 'Cancelada'
            WHERE idCita = %s AND idPaciente = %s
        """, (idCita, session.get('idUsuario')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Cita cancelada correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# DASHBOARD PROFESIONAL - STATS
# ============================================================
@app.route('/api/profesional/dashboard', methods=['GET'])
def dashboard_profesional():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idProfesional = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(DISTINCT idPaciente) as total FROM Citas
            WHERE idProfesional = %s AND estado != 'Cancelada'
        """, (idProfesional,))
        pacientes_activos = cursor.fetchone()['total']

        cursor.execute("""
            SELECT COUNT(*) as total FROM Citas
            WHERE idProfesional = %s AND fecha = CURDATE() AND estado != 'Cancelada'
        """, (idProfesional,))
        citas_hoy = cursor.fetchone()['total']

        cursor.execute("""
            SELECT COUNT(*) as total FROM Citas
            WHERE idProfesional = %s AND estado = 'Pendiente'
        """, (idProfesional,))
        citas_pendientes = cursor.fetchone()['total']

        cursor.execute("""
            SELECT r.nombre as paciente, c.fecha, c.hora, c.tipoCita, c.estado
            FROM Citas c
            JOIN Register r ON c.idPaciente = r.idUsuario
            WHERE c.idProfesional = %s AND c.estado != 'Cancelada'
            ORDER BY c.fecha DESC, c.hora DESC LIMIT 3
        """, (idProfesional,))
        actividades = cursor.fetchall()
        for a in actividades:
            if a.get('fecha'): a['fecha'] = a['fecha'].strftime('%d/%m/%Y')
            if a.get('hora'):  a['hora']  = str(a['hora'])

        return jsonify({
            'success':           True,
            'pacientes_activos': pacientes_activos,
            'citas_hoy':         citas_hoy,
            'citas_pendientes':  citas_pendientes,
            'actividades':       actividades
        })
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# PACIENTES - LISTAR CON ÚLTIMO DIAGNÓSTICO
# ============================================================
@app.route('/api/profesional/pacientes', methods=['GET'])
def listar_pacientes_profesional():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idProfesional = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT r.idUsuario, r.nombre, p.edad, p.genero,
                   COALESCE(p.numeroTelefonico, r.email) as contacto,
                   (SELECT diagnostico FROM Reportes
                    WHERE idPaciente = r.idUsuario
                    ORDER BY fechaInicio DESC LIMIT 1) as ultimoDiagnostico
            FROM Register r
            JOIN PerfilPaciente p ON r.idUsuario = p.idPaciente
            JOIN Citas c ON c.idPaciente = r.idUsuario
            WHERE c.idProfesional = %s AND r.rol = 'paciente'
            ORDER BY r.nombre
        """, (idProfesional,))
        pacientes = cursor.fetchall()
        return jsonify({'success': True, 'pacientes': pacientes})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# DIAGNÓSTICOS - GUARDAR
# ============================================================
@app.route('/api/diagnosticos/guardar', methods=['POST'])
def guardar_diagnostico():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data          = request.get_json()
    idPaciente    = data.get('idPaciente')
    idProfesional = session.get('idUsuario')
    fecha         = data.get('fecha_diagnostico')
    sintomas      = data.get('sintomas')
    diagnostico   = data.get('diagnostico')
    tratamiento   = data.get('tratamiento')

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE PacientesProfesional 
            SET sintomas = %s, diagnostico = %s, tratamiento = %s, fechaDiagnostico = %s
            WHERE idProfesional = %s AND idPaciente = %s
        """, (sintomas, diagnostico, tratamiento, fecha, idProfesional, idPaciente))
        
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO PacientesProfesional (idProfesional, idPaciente, sintomas, diagnostico, tratamiento, fechaDiagnostico)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (idProfesional, idPaciente, sintomas, diagnostico, tratamiento, fecha))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Diagnóstico guardado correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# DIAGNÓSTICOS - HISTORIAL
# ============================================================
@app.route('/api/diagnosticos/historial', methods=['GET'])
def historial_diagnosticos():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idProfesional = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT r.nombre as paciente,
                   pp.fechaDiagnostico as fechaRaw,
                   pp.sintomas,
                   pp.diagnostico,
                   pp.tratamiento
            FROM PacientesProfesional pp
            JOIN Register r ON pp.idPaciente = r.idUsuario
            WHERE pp.idProfesional = %s AND pp.diagnostico IS NOT NULL AND pp.diagnostico != ''
            ORDER BY pp.fechaDiagnostico DESC
        """, (idProfesional,))
        
        historial = cursor.fetchall()
        return jsonify({'success': True, 'historial': historial})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# REPORTES - LISTAR POR PROFESIONAL
# ============================================================
@app.route('/api/reportes/profesional', methods=['GET'])
def listar_reportes_profesional():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idProfesional = session.get('idUsuario')
    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(estado = 'Completado') as completados,
                   SUM(estado = 'Pendiente') as pendientes
            FROM Reportes WHERE idProfesional = %s
        """, (idProfesional,))
        stats = cursor.fetchone()

        cursor.execute("""
            SELECT rep.idReporte, rep.tipoReporte, rep.estado,
                   DATE_FORMAT(rep.fechaInicio, '%d/%m/%Y') as fechaInicio,
                   DATE_FORMAT(rep.fechaFin, '%d/%m/%Y') as fechaFin,
                   COALESCE(r.nombre, 'General') as paciente
            FROM Reportes rep
            LEFT JOIN Register r ON rep.idPaciente = r.idUsuario
            WHERE rep.idProfesional = %s
            ORDER BY rep.fechaInicio DESC
        """, (idProfesional,))
        reportes = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT r.idUsuario, r.nombre
            FROM Register r
            WHERE r.rol = 'paciente'
            ORDER BY r.nombre
        """)
        pacientes = cursor.fetchall()

        return jsonify({'success': True, 'stats': stats, 'reportes': reportes, 'pacientes': pacientes})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# REPORTES - CREAR
# ============================================================
@app.route('/api/reportes/crear', methods=['POST'])
def crear_reporte():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data          = request.get_json()
    idProfesional = session.get('idUsuario')
    idPaciente    = data.get('idPaciente') or None
    tipoReporte   = data.get('tipoReporte')
    fechaInicio   = data.get('fechaInicio') or None
    fechaFin      = data.get('fechaFin')    or None

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Reportes (idProfesional, idPaciente, tipoReporte, fechaInicio, fechaFin, estado)
            VALUES (%s, %s, %s, %s, %s, 'Completado')
        """, (idProfesional, idPaciente, tipoReporte, fechaInicio, fechaFin))
        conn.commit()
        return jsonify({'success': True, 'message': 'Reporte generado correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# REPORTES - EDITAR
# ============================================================
@app.route('/api/reportes/editar', methods=['POST'])
def editar_reporte():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data        = request.get_json()
    idReporte   = data.get('idReporte')
    tipoReporte = data.get('tipoReporte')
    estado      = data.get('estado')

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Reportes SET tipoReporte = %s, estado = %s
            WHERE idReporte = %s AND idProfesional = %s
        """, (tipoReporte, estado, idReporte, session.get('idUsuario')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Reporte actualizado correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# REPORTES - ELIMINAR
# ============================================================
@app.route('/api/reportes/eliminar', methods=['POST'])
def eliminar_reporte():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data      = request.get_json()
    idReporte = data.get('idReporte')

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM Reportes
            WHERE idReporte = %s AND idProfesional = %s
        """, (idReporte, session.get('idUsuario')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Reporte eliminado correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

# ============================================================
# EVOLUCIÓN PACIENTE - GUARDAR
# ============================================================
@app.route('/api/evolucion/guardar', methods=['POST'])
def guardar_evolucion():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    data             = request.get_json()
    idPaciente       = session.get('idUsuario')
    estadoEmocional  = data.get('estadoEmocional')
    nivelEnergia     = data.get('nivelEnergia')
    notasPersonales  = data.get('notasPersonales')

    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO EvolucionPaciente (idPaciente, estadoEmocional, nivelEnergia, notasPersonales)
            VALUES (%s, %s, %s, %s)
        """, (idPaciente, estadoEmocional, nivelEnergia, notasPersonales))
        conn.commit()
        return jsonify({'success': True, 'message': 'Evolución guardada correctamente'})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# EVOLUCIÓN PACIENTE - HISTORIAL
# ============================================================
@app.route('/api/evolucion/historial', methods=['GET'])
def historial_evolucion():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idPaciente = session.get('idUsuario')

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT estadoEmocional, nivelEnergia, notasPersonales,
                   DATE_FORMAT(fecha, '%d/%m/%Y') as fecha,
                   fecha as fechaRaw
            FROM EvolucionPaciente
            WHERE idPaciente = %s
            ORDER BY fecha DESC
        """, (idPaciente,))
        historial = cursor.fetchall()
        return jsonify({'success': True, 'historial': historial})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


# ============================================================
# EVOLUCIÓN PACIENTE - TODOS (PARA PROFESIONAL)
# ============================================================
@app.route('/api/evolucion/todos', methods=['GET'])
def evolucion_todos_pacientes():
    if 'usuario' not in session:
        return jsonify({'success': False, 'message': 'No autenticado'}), 401

    idProfesional = session.get('idUsuario')

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT e.estadoEmocional, e.nivelEnergia, e.notasPersonales,
                   DATE_FORMAT(e.fecha, '%d/%m/%Y') as fecha,
                   e.fecha as fechaRaw,
                   r.nombre as paciente
            FROM EvolucionPaciente e
            JOIN Register r ON e.idPaciente = r.idUsuario
            LEFT JOIN Citas c ON c.idPaciente = e.idPaciente AND c.idProfesional = %s
            WHERE c.idProfesional = %s OR c.idProfesional IS NULL
            ORDER BY e.fecha DESC
        """, (idProfesional, idProfesional))
        historial = cursor.fetchall()
        return jsonify({'success': True, 'historial': historial})
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

# ============================================================
# CITAS - FECHAS DISPONIBLES DEL MES
# ============================================================
@app.route('/api/citas/fechas-disponibles', methods=['POST'])
def fechas_disponibles():
    data          = request.get_json()
    idProfesional = data.get('idProfesional')
    anio          = data.get('anio')
    mes           = data.get('mes')

    print(f"DEBUG - fechas_disponibles: profesional={idProfesional}, anio={anio}, mes={mes}")

    if not idProfesional or not anio or not mes:
        return jsonify({'success': False, 'message': 'Datos incompletos'})

    try:
        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Traer todas las disponibilidades del mes
        cursor.execute("""
            SELECT fecha, hora_inicio, hora_fin
            FROM Disponibilidad
            WHERE idProfesional = %s
              AND YEAR(fecha) = %s
              AND MONTH(fecha) = %s
              AND estado = 'Disponible'
        """, (idProfesional, anio, mes))
        disponibilidades = cursor.fetchall()

        print(f"DEBUG - disponibilidades encontradas: {disponibilidades}")

        if not disponibilidades:
            return jsonify({'success': True, 'fechas': []})

        # Agrupar slots por fecha
        slots_por_fecha = {}
        for d in disponibilidades:
            fecha_str = d['fecha'].strftime('%Y-%m-%d')
            inicio = (datetime.min + d['hora_inicio']).time() if isinstance(d['hora_inicio'], timedelta) else d['hora_inicio']
            fin    = (datetime.min + d['hora_fin']).time()    if isinstance(d['hora_fin'], timedelta)    else d['hora_fin']

            if fecha_str not in slots_por_fecha:
                slots_por_fecha[fecha_str] = 0

            hora_actual = inicio
            while hora_actual < fin:
                slots_por_fecha[fecha_str] += 1
                dt_actual   = datetime.combine(date.today(), hora_actual)
                hora_actual = (dt_actual + timedelta(minutes=30)).time()

        # Contar citas ocupadas por fecha
        cursor.execute("""
            SELECT DATE_FORMAT(fecha, '%Y-%m-%d') as fecha, COUNT(*) as ocupadas
            FROM Citas
            WHERE idProfesional = %s
              AND YEAR(fecha) = %s
              AND MONTH(fecha) = %s
              AND estado != 'Cancelada'
            GROUP BY fecha
        """, (idProfesional, anio, mes))
        ocupadas_por_fecha = {row['fecha']: row['ocupadas'] for row in cursor.fetchall()}

        # Solo fechas con al menos un slot libre
        fechas_disponibles = [
            fecha for fecha, total_slots in slots_por_fecha.items()
            if ocupadas_por_fecha.get(fecha, 0) < total_slots
        ]

        return jsonify({'success': True, 'fechas': sorted(fechas_disponibles)})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
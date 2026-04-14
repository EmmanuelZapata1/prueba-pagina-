const API = 'http://127.0.0.1:5000';
let todosUsuarios = [];

document.addEventListener('DOMContentLoaded', () => {
    cargarUsuariosRoles();
    document.getElementById('buscarUsuario')?.addEventListener('input', filtrarUsuarios);
document.getElementById('filtroRol')?.addEventListener('change', filtrarUsuarios);
document.getElementById('filtroEstado')?.addEventListener('change', filtrarUsuarios);
    document.getElementById('btnAsignarRol')?.addEventListener('click', asignarRol);
});

async function cargarUsuariosRoles() {
    try {
        const res  = await fetch(`${API}/api/admin/roles/usuarios`);
        const data = await res.json();

        if (!data.success) return;

        todosUsuarios = data.usuarios;

        console.log("Usuarios cargados:", todosUsuarios); 

        renderTablaRoles(todosUsuarios);
        set('cntRolUsuarios', todosUsuarios.length);
        set('txtUsuariosEncontrados', todosUsuarios.length);

    } catch(e) { 
        console.error('Error roles:', e); 
    }

    cargarHistorial();
}

function renderTablaRoles(lista) {
    const tbody = document.getElementById('tablaUsuarios');
    if (!tbody) return;
    if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Sin usuarios.</td></tr>';
        return;
    }
    tbody.innerHTML = lista.map(u => {
        const ini = u.nombre.split(' ').map(p=>p[0]).join('').toUpperCase().slice(0,2);
        const nom = u.nombre.replace(/'/g,"\\'");
        return `
        <tr>
          <td>
            <div class="user-cell">
              <div class="user-avatar">${ini}</div>
              <div><div class="user-name">${u.nombre}</div><div class="user-email">${u.email}</div></div>
            </div>
          </td>
          <td>${rolBadge(u.rol)}</td>
          <td>${estadoBadge(u)}</td>
          <td class="text-muted" style="font-size:.82rem;">${u.fechaRegistro||'—'}</td>
          <td class="text-end">
            <div class="d-flex justify-content-end gap-1">
              <button class="btn btn-sm btn-outline-primary" onclick="abrirModalEditar(${u.idUsuario},'${nom}','${u.rol}')" title="Editar"><i class="fas fa-edit"></i></button>
            </div>
          </td>
        </tr>`;
    }).join('');
}

async function cargarHistorial() {
    try {
        const res  = await fetch(`${API}/api/admin/roles/historial`);
        const data = await res.json();
        if (!data.success) return;
        const tbody = document.getElementById('tablaHistorial');
        if (!tbody) return;
        set('cntHistorial', data.historial.length);
        if (!data.historial.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Sin historial de cambios.</td></tr>';
            return;
        }
        tbody.innerHTML = data.historial.map(h => `
        <tr>
          <td class="mono" style="font-size:.82rem;">${h.fecha||'—'}</td>
          <td style="font-size:.82rem;">${h.administrador||'Admin'}</td>
          <td><span class="log-badge role">${h.accion||'—'}</span></td>
          <td class="text-muted" style="font-size:.82rem;">${h.detalle||'—'}</td>
        </tr>`).join('');
    } catch(e) { console.error(e); }
}

// ── Modal editar rol ──────────────────────────────────────────────────────────
let _editRolId = null;
function abrirModalEditar(id, nombre, rolActual) {
    _editRolId = id;
    set('editarRolNombre', nombre);
    const sel = document.getElementById('selectNuevoRol');
    if (sel) sel.value = rolActual;
    new bootstrap.Modal(document.getElementById('modalEditarRol')).show();
}

async function guardarRol() {
    const nuevoRol = document.getElementById('selectNuevoRol')?.value;
    if (!nuevoRol || !_editRolId) return;
    try {
        const res  = await fetch(`${API}/api/admin/roles/cambiar`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idUsuario: _editRolId, nuevoRol })
        });
        const data = await res.json();
        bootstrap.Modal.getInstance(document.getElementById('modalEditarRol')).hide();
        mostrarAlerta(data.success ? 'success' : 'danger', data.message);
        if (data.success) cargarUsuariosRoles();
    } catch(e) { console.error(e); }
}

// ── Activar / Desactivar ──────────────────────────────────────────────────────
async function confirmarAccion(id, nombre, accion) {
    const acc = accion === 'desactivar' ? 'bloquear' : 'desbloquear';
    try {
        const res  = await fetch(`${API}/api/admin/usuarios/bloquear`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idUsuario: id, accion: acc })
        });
        const data = await res.json();
        mostrarAlerta(data.success ? 'success' : 'danger', data.message);
        if (data.success) cargarUsuariosRoles();
    } catch(e) { console.error(e); }
}

// ── Asignar rol por email ─────────────────────────────────────────────────────
async function asignarRol() {
    const email  = document.getElementById('emailUsuario')?.value.trim();
    const rol    = document.getElementById('nuevoRol')?.value;
    if (!email || !rol) {
        let camposFaltantes = [];
        if (!email) camposFaltantes.push('Email');
        if (!rol) camposFaltantes.push('Rol');
        return mostrarAlerta('error', `Falta: ${camposFaltantes.join(', ')}`);
    }
    const usuario = todosUsuarios.find(u => u.email === email);
    if (!usuario) return mostrarAlerta('danger', 'Usuario no encontrado.');
    try {
        const res  = await fetch(`${API}/api/admin/roles/cambiar`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idUsuario: usuario.idUsuario, nuevoRol: rol })
        });
        const data = await res.json();
        mostrarAlerta(data.success ? 'success' : 'danger', data.message);
        if (data.success) cargarUsuariosRoles();
    } catch(e) { console.error(e); }
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function mostrarTab(tab, btn) {
    ['usuarios','agregar','historial'].forEach(t => {
        const el = document.getElementById(`tab-${t}`);
        if (el) el.style.display = t === tab ? '' : 'none';
    });
    document.querySelectorAll('.roles-tab, .logs-tab, .notif-tab').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
}



function rolBadge(rol) {
    if (!rol) return '—';
    const clases = {
        paciente: 'badge-rol badge-rol-paciente',
        profesional: 'badge-rol badge-rol-profesional',
        admin: 'badge-rol badge-rol-admin'
    };
    return `<span class="${clases[rol] || 'badge-rol'}">${capitalizar(rol)}</span>`;
}

function estadoBadge(u) {
    if (u.activo == 0) return '<span class="badge bg-warning text-dark">Inactivo</span>';
    return '<span class="badge bg-success">Activo</span>';
}

function capitalizar(s) { return s ? s.charAt(0).toUpperCase()+s.slice(1) : ''; }
function set(id, val) { const el = document.getElementById(id); if(el) el.textContent = val; }

function mostrarAlerta(tipo, msg) {
    if (tipo === 'success') {
        PsyAIAlerts.success('Éxito', msg);
    } else {
        PsyAIAlerts.error('Error', msg);
    }
}

function abrirModalEliminarRol(id, nombre, rol) {
    // Por ahora solo muestra alerta — borrar rol = cambiar a sin rol no aplica en este sistema
    mostrarAlerta('warning', `Para eliminar el rol de ${nombre}, cámbialo desde "Editar rol".`);
}
function filtrarUsuarios() {
    console.log("FILTRO ACTIVADO");

    const texto  = document.getElementById('buscarUsuario')?.value.toLowerCase() || '';
    const rol    = document.getElementById('filtroRol')?.value || '';
    const estado = document.getElementById('filtroEstado')?.value || '';

console.log("Usuarios:", todosUsuarios);
    console.log("rol:", rol, "estado:", estado, "texto:", texto);

    const filtrados = todosUsuarios.filter(u => {
        const coincideTexto =
            u.nombre.toLowerCase().includes(texto) ||
            u.email.toLowerCase().includes(texto);

        const coincideRol =
            rol === '' || (u.rol && u.rol.toLowerCase() === rol);

        const coincideEstado =
            estado === '' ||
            (estado === 'activo' && parseInt(u.activo) === 1) ||
            (estado === 'inactivo' && parseInt(u.activo) === 0);

        return coincideTexto && coincideRol && coincideEstado;
    });

    renderTablaRoles(filtrados);
    set('txtUsuariosEncontrados', filtrados.length);
}
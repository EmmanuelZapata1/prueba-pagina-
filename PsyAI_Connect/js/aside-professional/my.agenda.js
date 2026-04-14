// ============================================================
// js/aside-professional/my.agenda.js — Mi Agenda Profesional
// ============================================================

function formatearHora(hora) {
    if (!hora) return '—';
    const partes = hora.split(':');
    const horaNum = parseInt(partes[0]);
    const minutos = partes[1] || '00';
    const periodo = horaNum >= 12 ? 'PM' : 'AM';
    const hora12 = horaNum > 12 ? horaNum - 12 : horaNum === 0 ? 12 : horaNum;
    return `${hora12}:${minutos} ${periodo}`;
}

document.addEventListener('DOMContentLoaded', function() {
    inicializarEventos();
    cargarDatosIniciales();
});

function inicializarEventos() {
    const btnDisponibilidad = document.getElementById("btnDisponibilidad");
    if (btnDisponibilidad) {
        btnDisponibilidad.addEventListener('click', guardarDisponibilidad);
    }

    const btnAgendar = document.getElementById("btnAgendarCita");
    if (btnAgendar) {
        btnAgendar.addEventListener('click', agendarCita);
    }

    const citaProfesional = document.getElementById("citaProfesional");
    if (citaProfesional) {
        citaProfesional.addEventListener('change', () => {
            const selectHora = document.getElementById("citaHora");
            if (selectHora) {
                selectHora.innerHTML = '<option value="">Selecciona una fecha primero</option>';
            }
            cargarHorariosDisponibles();
        });
    }

    const citaFecha = document.getElementById("citaFecha");
    if (citaFecha) {
        citaFecha.addEventListener('change', () => {
            cargarHorariosDisponibles();
        });
    }
}

async function cargarDatosIniciales() {
    await Promise.all([
        cargarPacientes(),
        cargarProfesionales(),
        cargarCitasProfesional()
    ]);
}

// ── Disponibilidad ──────────────────────────────────────────
async function guardarDisponibilidad() {
    const fecha       = document.getElementById("fecha").value;
    const hora_inicio = document.getElementById("hora_inicio").value;
    const hora_fin    = document.getElementById("hora_fin").value;

    if (!fecha || !hora_inicio || !hora_fin) {
        let camposFaltantes = [];
        if (!fecha) camposFaltantes.push('Fecha');
        if (!hora_inicio) camposFaltantes.push('Hora Inicio');
        if (!hora_fin) camposFaltantes.push('Hora Fin');
        PsyAIAlerts.warning('Campos Requeridos', `Falta: ${camposFaltantes.join(', ')}`);
        return;
    }

    const [h1, m1] = hora_inicio.split(':').map(Number);
    const [h2, m2] = hora_fin.split(':').map(Number);
    const minutosInicio = h1 * 60 + m1;
    const minutosFin = h2 * 60 + m2;
    const duracion = minutosFin - minutosInicio;

    if (duracion > 30) {
        PsyAIAlerts.warning('Límite Excedido', 'La sesión no puede exceder 30 minutos.');
        return;
    }
    if (duracion <= 0) {
        PsyAIAlerts.warning('Horario Inválido', 'La hora fin debe ser mayor a la hora inicio.');
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5000/api/disponibilidad/crear", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ fecha, hora_inicio, hora_fin })
        });

        const data = await response.json();
        if (data.success) {
            PsyAIAlerts.success('Disponibilidad Creada', 'Tu disponibilidad ha sido configurada correctamente.');
            document.getElementById('fecha').value = '';
            document.getElementById('hora_inicio').value = '';
            document.getElementById('hora_fin').value = '';
        } else {
            PsyAIAlerts.error('Error', data.message || 'No se pudo crear la disponibilidad.');
        }
    } catch(err) {
        console.error(err);
        PsyAIAlerts.error('Error', 'Error de conexión.');
    }
}

// ── Cargar Pacientes ─────────────────────────────────────────
async function cargarPacientes() {
    const select = document.getElementById("citaPaciente");
    if (!select) return;

    try {
        const res = await fetch("http://127.0.0.1:5000/api/pacientes/listar", {
            credentials: "include"
        });
        const data = await res.json();

        if (!data.success || !data.pacientes) return;

        select.innerHTML = '<option value="">Seleccionar paciente...</option>';
        data.pacientes.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.idUsuario;
            opt.textContent = p.nombre;
            select.appendChild(opt);
        });
    } catch(err) {
        console.error(err);
    }
}

// ── Cargar Profesionales ─────────────────────────────────────
async function cargarProfesionales() {
    const select = document.getElementById("citaProfesional");
    if (!select) return;

    try {
        const res = await fetch("http://127.0.0.1:5000/api/profesionales/listar", {
            credentials: "include"
        });
        const data = await res.json();

        if (!data.success || !data.profesionales) return;

        select.innerHTML = '<option value="">Seleccionar profesional...</option>';
        data.profesionales.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.idUsuario;
            opt.textContent = p.nombre;
            select.appendChild(opt);
        });
    } catch(err) {
        console.error(err);
    }
}

// ── Cargar Horarios Disponibles ──────────────────────────────
async function cargarHorariosDisponibles() {
    const idProfesional = document.getElementById("citaProfesional").value;
    const fecha = document.getElementById("citaFecha").value;
    const select = document.getElementById("citaHora");

    if (!select) return;

    if (!idProfesional || !fecha) {
        select.innerHTML = '<option value="">Selecciona profesional y fecha</option>';
        return;
    }

    select.innerHTML = '<option value="">Cargando...</option>';

    // Generar horarios fijos de 8 AM a 6 PM
    const generarHorariosFijos = () => {
        const horarios = [];
        for (let hora = 8; hora < 18; hora++) {
            horarios.push(`${String(hora).padStart(2, '0')}:00`);
            horarios.push(`${String(hora).padStart(2, '0')}:30`);
        }
        horarios.push("18:00");
        return horarios;
    };

    try {
        // Obtener horarios ya reservados
        const res = await fetch("http://127.0.0.1:5000/api/citas/disponibles", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ idProfesional, fecha })
        });
        const data = await res.json();
        const horariosReservados = data.horarios || [];

        const todosHorarios = generarHorariosFijos();
        const horariosDisponibles = todosHorarios.filter(h => !horariosReservados.includes(h));

        if (horariosDisponibles.length === 0) {
            select.innerHTML = '<option value="">No hay disponibilidad</option>';
            return;
        }

        const formatMostrar = (hora) => {
            const [h, m] = hora.split(':').map(Number);
            const esPM = h >= 12;
            const hora12 = h > 12 ? h - 12 : h;
            const ampm = esPM ? 'PM' : 'AM';
            return `${hora12}:${String(m).padStart(2, '0')} ${ampm}`;
        };

        const formatHoraFin = (hora) => {
            const [h, m] = hora.split(':').map(Number);
            let horaFin = h;
            let minFin = m + 30;
            if (minFin >= 60) {
                minFin = 0;
                horaFin = h + 1;
            }
            const esPM = horaFin >= 12;
            const hora12 = horaFin > 12 ? horaFin - 12 : horaFin;
            const ampm = esPM ? 'PM' : 'AM';
            return `${hora12}:${String(minFin).padStart(2, '0')} ${ampm}`;
        };

        select.innerHTML = '<option value="">Selecciona una hora</option>';

        horariosDisponibles.forEach(hora => {
            const opt = document.createElement("option");
            opt.value = hora;
            opt.textContent = `${formatMostrar(hora)} - ${formatHoraFin(hora)}`;
            select.appendChild(opt);
        });

    } catch(err) {
        console.error(err);
        select.innerHTML = '<option value="">Error al cargar</option>';
    }
}

// ── Agendar Cita ────────────────────────────────────────────
async function agendarCita() {
    const idPaciente = document.getElementById("citaPaciente").value;
    const idProfesional = document.getElementById("citaProfesional").value;
    const fecha = document.getElementById("citaFecha").value;
    const hora = document.getElementById("citaHora").value;
    const tipoCita = document.getElementById("citaTipo").value;
    const motivo = document.getElementById("citaMotivo").value;

    if (!idProfesional || !idPaciente || !fecha || !hora || !tipoCita || !motivo) {
        let camposFaltantes = [];
        if (!idProfesional) camposFaltantes.push('Profesional');
        if (!idPaciente) camposFaltantes.push('Paciente');
        if (!fecha) camposFaltantes.push('Fecha');
        if (!hora) camposFaltantes.push('Hora');
        if (!tipoCita) camposFaltantes.push('Tipo de Cita');
        if (!motivo) camposFaltantes.push('Motivo');
        PsyAIAlerts.warning('Campos Requeridos', `Falta: ${camposFaltantes.join(', ')}`);
        return;
    }

    try {
        const res = await fetch("http://127.0.0.1:5000/api/citas/crear-profesional", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ idPaciente, idProfesional, fecha, hora, tipoCita, motivo })
        });
        const data = await res.json();

        if (data.success) {
            PsyAIAlerts.success('Cita Agendada', 'La cita ha sido creada correctamente.');
            document.getElementById('citaProfesional').value = '';
            document.getElementById('citaPaciente').value = '';
            document.getElementById('citaFecha').value = '';
            document.getElementById('citaHora').value = '';
            document.getElementById('citaTipo').value = '';
            document.getElementById('citaMotivo').value = '';
            cargarCitasProfesional();
        } else {
            PsyAIAlerts.error('Error', data.message || 'No se pudo agendar la cita.');
        }
    } catch(err) {
        console.error(err);
        PsyAIAlerts.error('Error', 'Error de conexión.');
    }
}

// ── Cargar Citas del Profesional ────────────────────────────
async function cargarCitasProfesional() {
    const lista = document.getElementById("listaCitas");
    if (!lista) {
        console.error("No se encontró el elemento listaCitas");
        return;
    }

    lista.innerHTML = '<li class="list-group-item text-muted">Cargando...</li>';

    try {
        const res = await fetch("/api/citas/profesional", {
            credentials: "include"
        });
        
        if (!res.ok) {
            lista.innerHTML = '<li class="list-group-item text-danger">Error de conexión</li>';
            return;
        }
        
        const data = await res.json();

        if (!data.success || !data.citas || data.citas.length === 0) {
            lista.innerHTML = '<li class="list-group-item text-muted">No hay citas próximas</li>';
            return;
        }

        lista.innerHTML = data.citas.map(c => {
            const inicial = c.paciente ? c.paciente.charAt(0).toUpperCase() : '?';
            const fotoUrl = c.foto_perfil 
                ? `../uploads/${c.foto_perfil}` 
                : `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='35' height='35' viewBox='0 0 35 35'%3E%3Ccircle cx='17.5' cy='17.5' r='17.5' fill='%232196F3'/%3E%3Ctext x='17.5' y='21' text-anchor='middle' fill='white' font-family='Arial' font-size='12'%3E${inicial}%3C/text%3E%3C/svg%3E`;
            return `
                <li class="list-group-item d-flex align-items-center">
                    <img src="${fotoUrl}" alt="Foto" class="rounded-circle me-2" style="width:35px;height:35px;object-fit:cover;">
                    <div>
                        <strong>${c.paciente}</strong> - ${c.fecha} ${formatearHora(c.hora)}<br>
                        <small class="text-muted">${c.tipoCita}</small>
                        <span class="badge ${c.estado === 'Pendiente' ? 'bg-success' : c.estado === 'Cancelada' ? 'bg-danger' : 'bg-warning'} ms-2">${c.estado === 'Pendiente' ? 'Confirmada' : c.estado}</span>
                    </div>
                </li>
            `;
        }).join('');
    } catch(err) {
        console.error(err);
        lista.innerHTML = '<li class="list-group-item text-danger">Error al cargar citas</li>';
    }
}

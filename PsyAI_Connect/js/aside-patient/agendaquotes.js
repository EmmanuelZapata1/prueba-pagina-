function formatearHora(hora) {
  if (!hora) return '—';
  const partes = hora.split(':');
  const horaNum = parseInt(partes[0]);
  const minutos = parseInt(partes[1]) || 0;
  const periodo = horaNum >= 12 ? 'PM' : 'AM';
  const hora12 = horaNum === 0 ? 12 : horaNum > 12 ? horaNum - 12 : horaNum;
  const minutosFin = minutos + 30;
  let horaFin = horaNum;
  let minFinStr = String(minutos).padStart(2, '0');
  if (minutosFin >= 60) {
    horaFin = horaNum + 1;
    minFinStr = '00';
  }
  const horaFin12 = horaFin === 0 ? 12 : horaFin > 12 ? horaFin - 12 : horaFin;
  return `${hora12}:${String(minutos).padStart(2, '0')} - ${horaFin12}:${minFinStr} ${periodo}`;
}

function formatearHoraCorta(hora) {
  if (!hora) return '—';
  const partes = hora.split(':');
  const horaNum = parseInt(partes[0]);
  const minutos = partes[1] || '00';
  const periodo = horaNum >= 12 ? 'PM' : 'AM';
  const hora12 = horaNum > 12 ? horaNum - 12 : horaNum === 0 ? 12 : horaNum;
  return `${hora12}:${minutos} ${periodo}`;
}

async function cargarHorarios() {
  const idProfesional = parseInt(document.getElementById("profesional").value);
  const fecha         = document.getElementById("date").value;
  const select        = document.getElementById("time");
  const labelFecha    = document.getElementById("fechaSeleccionadaLabel");
  if (!idProfesional || !fecha) return;

  select.innerHTML = '<option value="">Cargando horarios...</option>';
  try {
    const res  = await fetch("/api/citas/disponibles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ idProfesional, fecha })
    });
    const data = await res.json();
    
    if (!data.horarios || data.horarios.length === 0) {
      select.innerHTML = '<option value="">No hay horarios disponibles para esta fecha</option>';
      select.disabled = true;
      const fechaSinHorarios = document.getElementById('date').value;
      if (fechaSinHorarios) {
        calFechasDisponibles = calFechasDisponibles.filter(f => f !== fechaSinHorarios);
      }
      document.getElementById('date').value = '';
      calFechaSeleccionada = '';
      labelFecha.textContent = '';
      labelFecha.innerHTML = '<span class="text-danger"><i class="fas fa-exclamation-triangle me-1"></i>No hay horarios disponibles para esta fecha</span>';
      setTimeout(() => { labelFecha.textContent = ''; }, 3000);
      dibujarDias();
      return;
    }
    
    calFechaSinHorarios = '';
    select.disabled = false;
    select.innerHTML = '<option value="">Selecciona una hora</option>';
    data.horarios.forEach(hora => {
      const partes = hora.split(':');
      const horaNum = parseInt(partes[0]);
      const minutos = parseInt(partes[1]) || 0;
      const periodo = horaNum >= 12 ? 'PM' : 'AM';
      const hora12 = horaNum === 0 ? 12 : horaNum > 12 ? horaNum - 12 : horaNum;
      const minutosFin = minutos + 30;
      let horaFin = horaNum;
      let minFinStr = String(minutos).padStart(2, '0');
      if (minutosFin >= 60) {
        horaFin = horaNum + 1;
        minFinStr = '00';
      }
      const horaFin12 = horaFin === 0 ? 12 : horaFin > 12 ? horaFin - 12 : horaFin;
      const opt = document.createElement("option");
      opt.value = hora;
      opt.textContent = `${hora12}:${String(minutos).padStart(2, '0')} - ${horaFin12}:${minFinStr} ${periodo}`;
      select.appendChild(opt);
    });
  } catch(e) {
    select.innerHTML = '<option value="">Error al cargar horarios</option>';
  }
}

// ============================================================
// CALENDARIO
// ============================================================
let calMes, calAnio, calFechasDisponibles = [], calFechaSeleccionada = '', calFechaSinHorarios = '';

function iniciarCalendario() {
  const hoy = new Date();
  calMes  = hoy.getMonth() + 1;
  calAnio = hoy.getFullYear();
}

async function renderCalendario() {
  const idProfesional = document.getElementById('profesional').value;
  const container     = document.getElementById('diasCalendario');
  const label         = document.getElementById('labelMes');
  const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  label.textContent = `${meses[calMes - 1]} ${calAnio}`;

  if (!idProfesional) {
    container.innerHTML = '<span style="font-size:.8rem;color:#aaa;grid-column:span 7">Selecciona un profesional primero</span>';
    return;
  }

  container.innerHTML = '<span style="font-size:.8rem;color:#aaa;grid-column:span 7">Cargando...</span>';

  try {
    const res  = await fetch('/api/citas/fechas-disponibles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ idProfesional, anio: calAnio, mes: calMes })
    });
    const data = await res.json();
    calFechasDisponibles = data.fechas || [];
  } catch(e) {
    calFechasDisponibles = [];
  }
  dibujarDias();
}

function dibujarDias() {
  const container  = document.getElementById('diasCalendario');
  container.innerHTML = '';
  const primerDia  = new Date(calAnio, calMes - 1, 1).getDay();
  const diasMes    = new Date(calAnio, calMes, 0).getDate();
  const offset     = (primerDia === 0) ? 6 : primerDia - 1;
  const hoy        = new Date();
  hoy.setHours(0, 0, 0, 0);

  const isDarkMode = document.documentElement.classList.contains('dark-mode');
  const colors = isDarkMode ? {
    bg: '#1a2a40', accent: '#64B5F6', text: '#1a2a40', muted: '#78909C'
  } : {
    bg: '#e3f2fd', accent: '#1976D2', text: '#ffffff', muted: '#9e9e9e'
  };

  for (let i = 0; i < offset; i++) container.innerHTML += '<span></span>';

  for (let d = 1; d <= diasMes; d++) {
    const fechaStr   = `${calAnio}-${String(calMes).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const fecha      = new Date(calAnio, calMes - 1, d);
    const pasado     = fecha < hoy;
    const disponible = calFechasDisponibles.includes(fechaStr);
    const sel        = calFechaSeleccionada === fechaStr;
    const sinHorarios = calFechaSinHorarios === fechaStr;

    let estilo = 'border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;margin:auto;font-size:.85rem;';
    let onclick = '';

    if (pasado) {
      estilo += `color:${colors.muted};cursor:not-allowed;`;
    } else if (sinHorarios) {
      estilo += `color:${colors.muted};cursor:not-allowed;`;
    } else if (disponible) {
      estilo += sel
        ? `background:${colors.accent};color:${colors.text};cursor:pointer;font-weight:600;box-shadow:0 2px 6px rgba(25,118,210,0.3);`
        : `background:${colors.bg};color:${colors.accent};cursor:pointer;font-weight:500;border:1.5px solid ${colors.accent};`;
      onclick = `onclick="seleccionarFecha('${fechaStr}', ${d})"`;
    } else {
      estilo += `color:${colors.muted};cursor:not-allowed;`;
    }

    container.innerHTML += `<div style="${estilo}" ${onclick}>${d}</div>`;
  }
}

function seleccionarFecha(fechaStr, dia) {
  calFechaSeleccionada = fechaStr;
  document.getElementById('date').value = fechaStr;
  document.getElementById('fechaSeleccionadaLabel').textContent = `Fecha seleccionada: ${dia}/${calMes}/${calAnio}`;
  dibujarDias();
  cargarHorarios();
}

// ============================================================
// CARGAR CITAS DEL PACIENTE
// ============================================================
async function cargarCitasPaciente() {
  const tbody   = document.getElementById("tablaCitas");
  const histDiv = document.getElementById("listaCitasRecientes");

  if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fas fa-spinner fa-spin"></i> Cargando...</td></tr>';
  if (histDiv) histDiv.innerHTML = '<div class="text-center text-muted py-3"><i class="fas fa-spinner fa-spin"></i> Cargando...</div>';

  try {
    const res  = await fetch("/api/citas/paciente", { credentials: "include" });
    const data = await res.json();

    if (!data.success || !data.citas || data.citas.length === 0) {
      if (tbody)   tbody.innerHTML   = '<tr><td colspan="5" class="text-center text-muted py-3">No tienes citas agendadas</td></tr>';
      if (histDiv) histDiv.innerHTML = '<div class="text-center text-muted py-3">No tienes citas en tu historial</div>';
      return;
    }

    // Separar próximas vs historial
    const hoy     = new Date(); hoy.setHours(0,0,0,0);
    const proximas = data.citas.filter(c => {
      const [d,m,a] = c.fecha.split('/');
      return new Date(a,m-1,d) >= hoy && c.estado !== 'Cancelada';
    });
    const historial = data.citas.filter(c => {
      const [d,m,a] = c.fecha.split('/');
      return new Date(a,m-1,d) < hoy || c.estado === 'Cancelada';
    });

    // Tabla próximas citas
    if (tbody) {
      if (proximas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">No tienes citas próximas</td></tr>';
      } else {
        tbody.innerHTML = proximas.map(c => {
          let horaFormateada = '—';
          if (c.hora) {
            const partes = c.hora.split(':');
            const horaNum = parseInt(partes[0]);
            const minutos = parseInt(partes[1]) || 0;
            const periodo = horaNum >= 12 ? 'PM' : 'AM';
            const hora12 = horaNum === 0 ? 12 : horaNum > 12 ? horaNum - 12 : horaNum;
            const minutosFin = minutos + 30;
            let horaFin = horaNum;
            let minFinStr = String(minutos).padStart(2, '0');
            if (minutosFin >= 60) {
              horaFin = horaNum + 1;
              minFinStr = '00';
            }
            const horaFin12 = horaFin === 0 ? 12 : horaFin > 12 ? horaFin - 12 : horaFin;
            horaFormateada = `${hora12}:${String(minutos).padStart(2, '0')} - ${horaFin12}:${minFinStr} ${periodo}`;
          }
          return `
          <tr class="align-middle">
            <td class="fw-semibold">${c.fecha}</td>
            <td class="text-dark fw-medium">${horaFormateada}</td>
            <td>${c.tipoCita}</td>
            <td>${c.profesional || '—'}</td>
            <td>
              <span class="badge bg-${c.estado === 'Confirmada' || c.estado === 'Pendiente' ? 'success' : c.estado === 'Cancelada' ? 'danger' : 'warning'} me-2">${c.estado === 'Pendiente' ? 'Confirmada' : c.estado}</span>
              ${c.estado !== 'Cancelada' ? `<button class="btn btn-danger btn-sm" onclick="cancelarCita(${c.idCita})">Cancelar</button>` : ''}
            </td>
          </tr>
        `}).join('');
      }
    }

    // Historial
    if (histDiv) {
      if (historial.length === 0) {
        histDiv.innerHTML = '<div class="text-center text-muted py-3">No hay citas en el historial</div>';
      } else {
        histDiv.innerHTML = historial.map(c => `
          <div class="list-group-item d-flex justify-content-between align-items-center">
            <div>
              <div class="fw-semibold">${c.tipoCita} — ${c.profesional || '—'}</div>
              <small class="text-muted">${c.fecha} - ${formatearHora(c.hora)}</small>
            </div>
            <span class="badge bg-${c.estado === 'Completada' ? 'success' : c.estado === 'Cancelada' ? 'danger' : 'secondary'}">${c.estado}</span>
          </div>
        `).join('');
      }
    }

  } catch(e) {
    console.error("Error cargando citas:", e);
    if (tbody)   tbody.innerHTML   = '<tr><td colspan="5" class="text-center text-muted py-3">No tienes citas agendadas</td></tr>';
    if (histDiv) histDiv.innerHTML = '<div class="text-center text-muted py-3">No hay citas en el historial</div>';
  }
}

async function cancelarCita(idCita) {
  citaAcancelar = idCita;
  modalCancelar.show();
}

// ============================================================
// CARGAR PROFESIONALES
// ============================================================
async function cargarProfesionales() {
  try {
    const res    = await fetch("/api/profesionales/listar", { credentials: "include" });
    const data   = await res.json();
    const select = document.getElementById("profesional");
    select.innerHTML = '<option value="">Seleccionar profesional</option>';
    (data.profesionales || []).forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.idUsuario;
      opt.textContent = p.nombre;
      select.appendChild(opt);
    });
  } catch(e) {
    console.error("Error cargando profesionales:", e);
  }
}

// ============================================================
// DOM LISTO
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  cargarProfesionales();
  iniciarCalendario();
  renderCalendario();
  cargarCitasPaciente();

  document.getElementById('btnMesAnterior').addEventListener('click', () => {
    calMes--; if (calMes < 1) { calMes = 12; calAnio--; }
    calFechaSeleccionada = '';
    calFechaSinHorarios = '';
    calFechasDisponibles = [];
    document.getElementById('date').value = '';
    document.getElementById('fechaSeleccionadaLabel').textContent = '';
    renderCalendario();
  });

  document.getElementById('btnMesSiguiente').addEventListener('click', () => {
    calMes++; if (calMes > 12) { calMes = 1; calAnio++; }
    calFechaSeleccionada = '';
    calFechaSinHorarios = '';
    calFechasDisponibles = [];
    document.getElementById('date').value = '';
    document.getElementById('fechaSeleccionadaLabel').textContent = '';
    renderCalendario();
  });

  window.addEventListener('themeChanged', () => dibujarDias());

  document.getElementById('profesional').addEventListener('change', () => {
    calFechaSeleccionada = '';
    calFechaSinHorarios = '';
    calFechasDisponibles = [];
    document.getElementById('date').value = '';
    document.getElementById('fechaSeleccionadaLabel').textContent = '';
    document.getElementById('time').innerHTML = '<option value="">Selecciona profesional y fecha para ver disponibilidad</option>';
    renderCalendario();
  });

  const facturaModal   = new bootstrap.Modal(document.getElementById("facturaModal"));
  const modalPagoFinal = new bootstrap.Modal(document.getElementById("modalPagoFinal"));
  window.citaAcancelar = null;
  window.modalCancelar = new bootstrap.Modal(document.getElementById("modalCancelar"));

  document.getElementById("btnConfirmarCancelar").addEventListener("click", async () => {
    if (!citaAcancelar) return;
    try {
      const res  = await fetch("/api/citas/cancelar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ idCita: citaAcancelar })
      });
      const data = await res.json();
      modalCancelar.hide();
      citaAcancelar = null;
      if (data.success) {
        PsyAIAlerts.success('Cita Cancelada', 'Tu cita ha sido cancelada exitosamente.');
        cargarCitasPaciente();
      } else {
        PsyAIAlerts.error('Error', data.message || 'No se pudo cancelar.');
      }
    } catch(e) {
      PsyAIAlerts.error('Error', 'Error de conexión.');
    }
  });

  function validarFormularioCita() {
    const tipoCita = document.getElementById("tipoCita").value.trim();
    const fecha    = document.getElementById("date").value.trim();
    const hora     = document.getElementById("time").value.trim();
    const motivo   = document.getElementById("motivo").value.trim();
    if (!tipoCita || !fecha || !hora || !motivo) {
      PsyAIAlerts.error('Error', 'Llena todos los campos antes de continuar.');
      return false;
    }
    return true;
  }

  document.getElementById("btnSolicitarCita").addEventListener("click", () => {
    if (!validarFormularioCita()) return;
    facturaModal.show();
  });

  document.getElementById("btnContinuarPago").addEventListener("click", () => {
    const monto  = document.getElementById("montoPagoModal").value.trim();
    const metodo = document.getElementById("metodoPagoModal").value.trim();
    if (!monto || !metodo) { PsyAIAlerts.error('Error', 'Llena todos los campos.'); return; }

    const tituloEl    = document.getElementById("tituloMetodoPago");
    const contenidoEl = document.getElementById("contenidoMetodoPago");
    contenidoEl.innerHTML = "";

    if (metodo === "banco") {
      tituloEl.textContent = "Transferencia Bancaria";
      contenidoEl.innerHTML = `
        <div class="mb-3"><label class="form-label fw-semibold">Banco</label>
          <select id="banco" class="form-select">
            <option value="">Selecciona un banco</option>
            <option>Bancolombia</option><option>Davivienda</option><option>Banco de Bogotá</option>
            <option>BBVA</option><option>Scotiabank</option><option>Otro</option>
          </select></div>
        <div class="mb-3"><label class="form-label fw-semibold">Número de cuenta</label>
          <input type="text" id="numeroCuenta" class="form-control" placeholder="1234567890"></div>
        <div class="mb-3"><label class="form-label fw-semibold">Titular</label>
          <input type="text" id="titularCuenta" class="form-control"></div>
        <div class="mb-3"><label class="form-label fw-semibold">Tipo de cuenta</label>
          <select id="tipoCuenta" class="form-control">
            <option value="">Seleccionar</option><option value="ahorros">Ahorros</option><option value="corriente">Corriente</option>
          </select></div>`;
    } else if (metodo === "tarjeta") {
      tituloEl.textContent = "Tarjeta Crédito / Débito";
      contenidoEl.innerHTML = `
        <div class="mb-3"><label class="form-label fw-semibold">Número de tarjeta</label>
          <input type="text" id="numTarjeta" class="form-control" placeholder="XXXX XXXX XXXX XXXX"></div>
        <div class="mb-3"><label class="form-label fw-semibold">Titular</label>
          <input type="text" id="titularTarjeta" class="form-control"></div>
        <div class="mb-3"><label class="form-label fw-semibold">CVV</label>
          <input type="text" id="cvv" class="form-control" placeholder="123"></div>
        <div class="mb-3"><label class="form-label fw-semibold">Vencimiento</label>
          <input type="month" id="vencimiento" class="form-control"></div>`;
    }

    facturaModal.hide();
    modalPagoFinal.show();
  });

  document.getElementById("btnAtras").addEventListener("click", () => {
    modalPagoFinal.hide();
    facturaModal.show();
  });

  document.getElementById("btnFinalizarPago").addEventListener("click", async () => {
    const metodo = document.getElementById("metodoPagoModal").value.trim();
    let valid = true;

    if (metodo === "banco") {
      if (!document.getElementById("banco").value.trim() ||
          !document.getElementById("numeroCuenta").value.trim() ||
          !document.getElementById("titularCuenta").value.trim() ||
          !document.getElementById("tipoCuenta").value.trim()) valid = false;
    } else if (metodo === "tarjeta") {
      if (!document.getElementById("numTarjeta").value.trim() ||
          !document.getElementById("titularTarjeta").value.trim() ||
          !document.getElementById("cvv").value.trim() ||
          !document.getElementById("vencimiento").value.trim()) valid = false;
    }

    if (!valid) { PsyAIAlerts.error('Error', 'Pago rechazado, llena todos los campos.'); return; }

    const tipoCita      = document.getElementById("tipoCita").value;
    const fecha         = document.getElementById("date").value;
    const hora          = document.getElementById("time").value;
    const motivo        = document.getElementById("motivo").value;
    const idProfesional = document.getElementById("profesional").value;

    try {
      const res    = await fetch("/api/citas/crear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ tipoCita, fecha, hora, motivo, idProfesional })
      });
      const result = await res.json();

      if (result.success) {
        modalPagoFinal.hide();
        PsyAIAlerts.success('Éxito', result.message);
        cargarCitasPaciente();
      } else {
        PsyAIAlerts.error('Error', result.message);
      }
    } catch(e) {
      PsyAIAlerts.error('Error', 'Error al conectar con el servidor.');
    }
  });
});
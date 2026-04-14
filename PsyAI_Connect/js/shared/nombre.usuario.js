// ============================================================
// js/shared/nombre.usuario.js — Cargar nombre de usuario en header
// ============================================================

document.addEventListener('DOMContentLoaded', async function() {
    await cargarNombreUsuario();
});

async function cargarNombreUsuario() {
    try {
        const res = await fetch("/api/session", {
            credentials: "include"
        });
        
        if (res.status === 401) {
            return;
        }
        
        const data = await res.json();

        if (data.success && data.usuario) {
            const nombre = data.usuario.nombre || data.usuario.email?.split('@')[0] || 'Usuario';
            const rol = data.usuario.rol || data.usuario.role || '';

            actualizarNombresEnPagina(nombre, rol);
            cargarFotoPerfil(data);
        }
    } catch(err) {
        console.error("Error cargando usuario:", err);
    }
}

function cargarFotoPerfil(data) {
    const fotoPerfil = data.usuario?.fotoPerfil || data.fotoPerfil;
    const userInfoElements = document.querySelectorAll('.user-info');
    const nombre = data.usuario?.nombre || '';
    const inicial = nombre ? nombre.charAt(0).toUpperCase() : '?';
    
    userInfoElements.forEach(el => {
        if (!el.querySelector('.user-foto-perfil')) {
            const img = document.createElement('img');
            
            if (fotoPerfil) {
                img.src = fotoPerfil.startsWith('http') ? fotoPerfil : 'uploads/' + fotoPerfil;
            } else {
                img.src = `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%232196F3'/%3E%3Ctext x='20' y='24' text-anchor='middle' fill='white' font-family='Arial' font-size='14'%3E${inicial}%3C/text%3E%3C/svg%3E`;
            }
            
            img.className = 'user-foto-perfil rounded-circle me-2';
            img.style.width = '40px';
            img.style.height = '40px';
            img.style.objectFit = 'cover';
            img.style.marginRight = '10px';
            
            if (el.firstChild) {
                el.insertBefore(img, el.firstChild);
            } else {
                el.appendChild(img);
            }
        }
    });
}

function actualizarNombresEnPagina(nombre, rol) {
    const elementos = document.querySelectorAll('#nombrePaciente, #nombreProfesional, #nombrPaciente, .user-info span');
    
    elementos.forEach(el => {
        if (!el) return;
        
        if (el.id === 'nombrePaciente' || el.id === 'nombrPaciente') {
            el.textContent = `Hola, ${nombre}`;
        } else if (el.id === 'nombreProfesional') {
            const prefijo = (rol === 'profesional' || rol === 'professional') ? 'Dr(a). ' : '';
            el.textContent = `Hola, ${prefijo}${nombre}`;
        } else if (el.textContent.includes('Hola')) {
            el.textContent = `Hola, ${nombre}`;
        }
    });

    const headerSpans = document.querySelectorAll('.user-info span');
    headerSpans.forEach(span => {
        if (span.textContent.trim() === '' || span.textContent === 'Hola, ') {
            span.textContent = `Hola, ${nombre}`;
        }
    });
}

function getNombreUsuario() {
    const storedUser = localStorage.getItem('usuario') || localStorage.getItem('sessionUser');
    if (storedUser) {
        try {
            const usuario = JSON.parse(storedUser);
            return usuario.nombre || usuario.email?.split('@')[0] || 'Usuario';
        } catch(e) {
            return 'Usuario';
        }
    }
    return 'Usuario';
}

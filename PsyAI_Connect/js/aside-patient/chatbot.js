// ============================================================
// js/aside-patient/chatbot.js — Chatbot Emocional
// ============================================================

let historialChat = [];
const MAX_MENSAJES = 50;

document.addEventListener('DOMContentLoaded', function() {
    inicializarChat();
    configurarFormulario();
});

function inicializarChat() {
    const chatContainer = document.querySelector('#chatbot-section .border');
    if (!chatContainer) return;

    const stored = localStorage.getItem('chatbotHistorial');
    if (stored) {
        try {
            historialChat = JSON.parse(stored);
            if (historialChat.length > 0) {
                renderizarMensajes();
                return;
            }
        } catch(e) {
            console.error('Error parsing chat history:', e);
        }
    }

    chatContainer.innerHTML = `
        <div class="text-muted mb-2">
            <i class="fas fa-robot me-1"></i> <strong>PsyAI:</strong> ¡Hola! Soy tu asistente emocional. ¿Cómo te sientes hoy?
        </div>
    `;
}

function renderizarMensajes() {
    const chatContainer = document.querySelector('#chatbot-section .border');
    if (!chatContainer) return;

    chatContainer.innerHTML = historialChat.map(m => {
        if (m.tipo === 'usuario') {
            return `<div class="text-end text-primary mb-2">
                <strong>Tú:</strong> ${m.mensaje}
            </div>`;
        } else {
            return `<div class="text-muted mb-2">
                <i class="fas fa-robot me-1"></i> <strong>PsyAI:</strong> ${m.mensaje}
            </div>`;
        }
    }).join('');

    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function configurarFormulario() {
    const form = document.querySelector('#chatbot-section form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const input = form.querySelector('input[name="mensaje"]');
        const mensaje = input.value.trim();
        
        if (!mensaje) return;

        agregarMensajeUsuario(mensaje);
        input.value = '';

        await enviarMensaje(mensaje);
    });
}

function agregarMensajeUsuario(mensaje) {
    historialChat.push({ tipo: 'usuario', mensaje: mensaje });
    guardarHistorial();
    renderizarMensajes();
}

function agregarMensajeBot(mensaje) {
    historialChat.push({ tipo: 'bot', mensaje: mensaje });
    guardarHistorial();
    renderizarMensajes();
}

function guardarHistorial() {
    if (historialChat.length > MAX_MENSAJES) {
        historialChat = historialChat.slice(-MAX_MENSAJES);
    }
    localStorage.setItem('chatbotHistorial', JSON.stringify(historialChat));
}

async function enviarMensaje(mensaje) {
    const chatContainer = document.querySelector('#chatbot-section .border');
    if (chatContainer) {
        chatContainer.innerHTML += `
            <div class="text-muted mb-2">
                <i class="fas fa-spinner fa-spin me-1"></i> <strong>PsyAI:</strong> Escribiendo...
            </div>
        `;
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    try {
        const res = await fetch("http://127.0.0.1:5000/api/chatbot/enviar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ mensaje: mensaje })
        });
        const data = await res.json();

        if (data.respuesta) {
            agregarMensajeBot(data.respuesta);
        } else {
            agregarMensajeBot("Disculpa, no pude procesar tu mensaje. ¿Podrías intentarlo de nuevo?");
        }
    } catch(err) {
        console.error("Error chatbot:", err);
        
        const respuestasDefault = [
            "Entiendo cómo te sientes. ¿Quieres contarme más sobre eso?",
            "Gracias por compartirlo. ¿Hay algo más que quieras contarme?",
            "Es normal sentirse así. ¿Qué crees que te ayuda a sentirte mejor?",
            "Tu bienestar emocional es importante. ¿Cómo has estado durmiendo lately?"
        ];
        
        const respuestaAleatoria = respuestasDefault[Math.floor(Math.random() * respuestasDefault.length)];
        agregarMensajeBot(respuestaAleatoria);
    }
}

function limpiarChat() {
    historialChat = [];
    localStorage.removeItem('chatbotHistorial');
    inicializarChat();
}

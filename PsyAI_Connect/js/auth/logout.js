async function cerrarSesion() {
  await fetch('http://127.0.0.1:5000/api/logout', {
    method: 'POST',
    credentials: 'include'
  });
  window.location.href = '../index.html';
}
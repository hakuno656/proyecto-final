async function refreshStatus() {
  const parking = document.getElementById("parking");
  const barrier = document.getElementById("barrier");
  const connection = document.getElementById("connection");
  const distance = document.getElementById("distance");
  const mode = document.getElementById("mode");

  try {
    const response = await fetch("/estado", { cache: "no-store" });
    const data = await response.json();

    if (!response.ok || !data.conectado) {
      connection.textContent = "DESCONECTADO";
      connection.className = "state bad";
      parking.textContent = "SIN CONEXIÓN";
      parking.className = "state neutral";
      barrier.textContent = "--";
      barrier.className = "state neutral";
      distance.textContent = "Distancia: -- cm";
      mode.textContent = "Modo: --";
      return;
    }

    connection.textContent = "CONECTADO";
    connection.className = "state good";

    parking.textContent = data.ocupado ? "OCUPADO" : "DISPONIBLE";
    parking.className = "state " + (data.ocupado ? "bad" : "good");

    barrier.textContent = data.barrera ? "ABIERTA" : "CERRADA";
    barrier.className = "state " + (data.barrera ? "good" : "neutral");

    distance.textContent = "Distancia: " +
      (data.distancia === null ? "--" : Number(data.distancia).toFixed(1)) + " cm";
    mode.textContent = "Modo: " + (data.automatico ? "Automático" : "Manual");
  } catch (error) {
    connection.textContent = "ERROR DE CONEXIÓN";
    connection.className = "state bad";
  }
}

async function sendCommand(action) {
  const feedback = document.getElementById("feedback");
  try {
    const response = await fetch("/comando", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ accion: action })
    });
    const result = await response.json();
    feedback.textContent = result.mensaje || (result.ok ? "Comando enviado" : "No se pudo enviar");
    feedback.className = "feedback " + (result.ok ? "good" : "bad");
    await refreshStatus();
  } catch (error) {
    feedback.textContent = "Error de comunicación con el servidor";
    feedback.className = "feedback bad";
  }
}

async function registerExit() {
  if (confirm("Confirma que el automóvil ya salió físicamente del estacionamiento.")) {
    await sendCommand("EXIT");
  }
}

refreshStatus();
setInterval(refreshStatus, 1000);

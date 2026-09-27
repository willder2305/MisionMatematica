import React, { useState } from "react";
import logoMision from "../assets/pixel/logo_mision_matematica_pixel.png";
import { solicitarRecuperacionPassword } from "../services/authService";
import { navegarInternamente } from "../services/navigationService";

const ForgotPasswordPage = () => {
  const [correo, setCorreo] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  const enviar = async (evento) => {
    // Solicita recuperacion sin revelar si el correo existe.
    evento.preventDefault();
    setCargando(true);
    setMensaje("");
    try {
      const respuesta = await solicitarRecuperacionPassword(correo);
      setMensaje(respuesta.message || "Si el correo existe, recibirá instrucciones de recuperación.");
    } catch (error) {
      setMensaje(error.response?.data?.message || "No fue posible solicitar la recuperación.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={enviar}>
        <img className="auth-logo pixel-art" src={logoMision} alt="Misión Matemática" decoding="async" />
        <h1>Recuperar contraseña</h1>
        <p className="auth-welcome">Escribe tu correo para recibir instrucciones de recuperación.</p>
        {mensaje && <div className="auth-error neutral">{mensaje}</div>}
        <label>
          Correo electrónico
          <input name="correo" type="email" autoComplete="email" value={correo} onChange={(evento) => setCorreo(evento.target.value)} required />
        </label>
        <button type="submit" disabled={cargando}>{cargando ? "Enviando..." : "Enviar instrucciones"}</button>
        <button type="button" className="auth-text-button" onClick={() => navegarInternamente("/login")}>
          Volver al login
        </button>
      </form>
    </main>
  );
};

export default ForgotPasswordPage;

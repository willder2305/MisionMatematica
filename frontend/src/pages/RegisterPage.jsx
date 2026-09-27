import React, { useState } from "react";
import logoMision from "../assets/pixel/logo_mision_matematica_pixel.png";
import { registrar } from "../services/authService";
import { navegarInternamente } from "../services/navigationService";

const RegisterPage = () => {
  const [formulario, setFormulario] = useState({
    nombres: "",
    apellidos: "",
    correo: "",
    password: "",
    rol: "estudiante",
  });
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  const cambiarCampo = (evento) => {
    // Actualiza el estado local de registro.
    const { name, value } = evento.target;
    setFormulario((actual) => ({ ...actual, [name]: value }));
  };

  const enviar = async (evento) => {
    // Crea la cuenta y guarda la sesion devuelta por backend.
    evento.preventDefault();
    setCargando(true);
    setMensaje("");
    try {
      await registrar(formulario);
      navegarInternamente("/onboarding", { replace: true });
    } catch (error) {
      setMensaje(error.response?.data?.message || "No fue posible crear la cuenta.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={enviar}>
        <img className="auth-logo pixel-art" src={logoMision} alt="Misión Matemática" decoding="async" />
        <h1>Crear cuenta</h1>
        {mensaje && <div className="auth-error">{mensaje}</div>}
        <label>
          Nombres
          <input name="nombres" autoComplete="given-name" value={formulario.nombres} onChange={cambiarCampo} required />
        </label>
        <label>
          Apellidos
          <input name="apellidos" autoComplete="family-name" value={formulario.apellidos} onChange={cambiarCampo} required />
        </label>
        <label>
          Correo
          <input name="correo" type="email" autoComplete="email" value={formulario.correo} onChange={cambiarCampo} required />
        </label>
        <label>
          Contraseña
          <input name="password" type="password" minLength={8} autoComplete="new-password" value={formulario.password} onChange={cambiarCampo} required />
        </label>
        <label>
          Tipo de usuario
          <select name="rol" value={formulario.rol} onChange={cambiarCampo}>
            <option value="estudiante">Estudiante</option>
            <option value="docente">Docente</option>
          </select>
        </label>
        <button type="submit" disabled={cargando}>{cargando ? "Creando..." : "Crear cuenta"}</button>
        <button type="button" className="auth-text-button" onClick={() => navegarInternamente("/login")}>
          Ya tengo cuenta
        </button>
      </form>
    </main>
  );
};

export default RegisterPage;

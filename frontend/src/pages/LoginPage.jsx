import React, { useEffect, useState } from "react";
import logoMision from "../assets/pixel/logo_mision_matematica_pixel.png";
import personajeNino from "../assets/juego/sprits/sprit M1/S1Venfrente.png";
import personajeNina from "../assets/juego/sprits/sprit F1/S1Venfrente.png";
import ResponsiveModal from "../components/ui/ResponsiveModal";
import { login } from "../services/authService";
import { navegarInternamente } from "../services/navigationService";

const frases = [
  "Cada respuesta te hace avanzar.",
  "Supera desafíos matemáticos.",
  "Aprende a tu propio ritmo.",
];

const simbolos = ["+", "-", "x", "/", "%", "√", "7", "12"];

const LoginPage = () => {
  const [formulario, setFormulario] = useState({ correo: "", password: "" });
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [capsLockActivo, setCapsLockActivo] = useState(false);
  const [fraseActiva, setFraseActiva] = useState(0);
  const [recuperacionAbierta, setRecuperacionAbierta] = useState(false);

  useEffect(() => {
    // Rota microfrases educativas sin afectar la navegacion ni la sesion.
    const intervalo = window.setInterval(() => {
      setFraseActiva((actual) => (actual + 1) % frases.length);
    }, 3600);
    return () => window.clearInterval(intervalo);
  }, []);

  const rutaPorUsuario = (usuario) => {
    if (!usuario.onboarding_completado) return "/onboarding";
    if (usuario.rol === "estudiante") return "/juego";
    if (usuario.rol === "docente") return "/reportes";
    if (usuario.rol === "administrador") return "/admin";
    return "/login";
  };

  const cambiarCampo = (evento) => {
    // Mantiene sincronizados los campos del formulario de acceso.
    const { name, value } = evento.target;
    setFormulario((actual) => ({ ...actual, [name]: value }));
  };

  const enviar = async (evento) => {
    // Autentica contra Flask y redirige al juego/panel inicial.
    evento.preventDefault();
    if (cargando) return;
    setCargando(true);
    setMensaje("");
    try {
      const respuesta = await login(formulario);
      const usuario = respuesta.data.usuario;
      navegarInternamente(rutaPorUsuario(usuario), { replace: true });
    } catch (error) {
      const status = error.response?.status;
      if (!error.response) {
        setMensaje("No pudimos conectar con el servidor. Intenta nuevamente.");
      } else if (status === 401) {
        setMensaje("No pudimos iniciar sesión. Revisa tu correo y contraseña.");
      } else {
        setMensaje("Ocurrió un problema al iniciar sesión. Intenta nuevamente.");
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <main className="auth-page login-page">
      <div className="login-symbols" aria-hidden="true">
        {simbolos.map((simbolo, indice) => (
          <span key={`${simbolo}-${indice}`} className={`login-symbol symbol-${indice + 1}`}>{simbolo}</span>
        ))}
      </div>

      <section className="login-visual" aria-label="Bienvenida a Misión Matemática">
        <img className="login-logo pixel-art" src={logoMision} alt="Misión Matemática" decoding="async" />
        <div className="login-character-row" aria-hidden="true">
          <img className="login-character pixel-art character-boy" src={personajeNino} alt="" decoding="async" />
          <div className="login-orbit">
            <span>+</span>
            <span>x</span>
            <span>%</span>
          </div>
          <img className="login-character pixel-art character-girl" src={personajeNina} alt="" decoding="async" />
        </div>
        <div className="login-copy">
          <h1>Comienza tu aventura matemática</h1>
          <p>Aprende, supera desafíos y avanza a tu propio ritmo.</p>
          <strong key={fraseActiva}>{frases[fraseActiva]}</strong>
        </div>
      </section>

      <form className={`auth-card login-card ${mensaje ? "has-error" : ""}`} onSubmit={enviar} noValidate>
        <div className="login-card-heading">
          <span className="login-card-badge">Misión activa</span>
          <h2>Bienvenido de nuevo</h2>
          <p>Continúa tu aventura matemática.</p>
        </div>

        {mensaje && <div className="auth-error" role="alert">{mensaje}</div>}

        <label className="login-field">
          <span>Correo electrónico</span>
          <span className="login-input-wrap">
            <span className="login-input-icon" aria-hidden="true">@</span>
            <input
              name="correo"
              type="email"
              autoComplete="email"
              placeholder="tu@email.com"
              value={formulario.correo}
              onChange={cambiarCampo}
              required
            />
          </span>
        </label>

        <label className="login-field">
          <span>Contraseña</span>
          <span className="login-input-wrap password-field">
            <span className="login-input-icon" aria-hidden="true">*</span>
            <input
              name="password"
              type={mostrarPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="••••••••"
              value={formulario.password}
              onChange={cambiarCampo}
              onKeyUp={(evento) => setCapsLockActivo(evento.getModifierState?.("CapsLock") || false)}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setMostrarPassword((actual) => !actual)}
              aria-label={mostrarPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              title={mostrarPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            >
              {mostrarPassword ? "Ocultar" : "Ver"}
            </button>
          </span>
          {capsLockActivo && <small className="login-caps-warning">Bloq Mayús está activado.</small>}
        </label>

        <button type="submit" className="login-submit" disabled={cargando}>
          {cargando ? "Entrando..." : "Iniciar aventura"}
        </button>

        <div className="login-actions">
          <span>¿Aún no tienes cuenta?</span>
          <button type="button" className="auth-text-button" onClick={() => navegarInternamente("/registro")}>
            Crear cuenta
          </button>
        </div>
        <button type="button" className="auth-text-button login-forgot" onClick={() => setRecuperacionAbierta(true)}>
          ¿Olvidaste tu contraseña?
        </button>
      </form>
      <ResponsiveModal abierto={recuperacionAbierta} onCerrar={() => setRecuperacionAbierta(false)} titulo="Recuperar contraseña">
        <h2>Recuperar contraseña</h2>
        <p>Para recuperar el acceso a tu cuenta, contacta con el administrador.</p>
        <p><a href="mailto:wruizh1@miumg.edu.gt">wruizh1@miumg.edu.gt</a></p>
        <div className="modal-actions">
          <button type="button" onClick={() => setRecuperacionAbierta(false)}>Entendido</button>
        </div>
      </ResponsiveModal>
    </main>
  );
};

export default LoginPage;

import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import { confirmarActualizacionGrado, validarActualizacionGrado } from "../services/gruposService";
import { navegarInternamente } from "../services/navigationService";
import { obtenerOnboarding } from "../services/onboardingService";

const ActualizarGradoPage = () => {
  const [pin, setPin] = useState("");
  const [confirmacion, setConfirmacion] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });

  useEffect(() => {
    let activo = true;
    obtenerOnboarding()
      .then((respuesta) => {
        if (activo && respuesta.data?.perfil?.modalidad !== "grupo_educativo") {
          navegarInternamente("/panel-estudiante", { replace: true });
        }
      })
      .catch(() => {
        if (activo) {
          navegarInternamente("/panel-estudiante", { replace: true });
        }
      });
    return () => {
      activo = false;
    };
  }, []);

  const validar = async (evento) => {
    // Valida el PIN y muestra el nuevo contexto sin modificar la matricula.
    evento.preventDefault();
    setCargando(true);
    setMensaje({ tipo: "", texto: "" });
    setConfirmacion(null);
    try {
      const respuesta = await validarActualizacionGrado(pin);
      setConfirmacion(respuesta.data);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  const confirmar = async () => {
    // Aplica el cambio de ciclo y vuelve al panel del estudiante.
    setCargando(true);
    setMensaje({ tipo: "", texto: "" });
    try {
      await confirmarActualizacionGrado(pin);
      setMensaje({ tipo: "success", texto: "Grado actualizado correctamente." });
      setTimeout(() => navegarInternamente("/panel-estudiante", { replace: true }), 700);
    } catch (error) {
      setMensaje({ tipo: "error", texto: error.message });
    } finally {
      setCargando(false);
    }
  };

  return (
    <section className="content update-grade-page">
      <div className="header-row">
        <div>
          <h1>Actualizar grado</h1>
          <p>Ingresa el nuevo PIN de tu grupo educativo.</p>
        </div>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      <section className="panel update-grade-panel">
        <form onSubmit={validar}>
          <label>
            Nuevo PIN
            <input
              value={pin}
              inputMode="numeric"
              maxLength={6}
              minLength={6}
              onChange={(evento) => setPin(evento.target.value.replace(/\D/g, "").slice(0, 6))}
              required
            />
          </label>
          <button type="submit" className="pixel-primary-button success" disabled={cargando || pin.length !== 6}>
            {cargando ? "Validando..." : "Validar PIN"}
          </button>
        </form>

        {confirmacion?.nuevo && (
          <div className="update-grade-confirmation">
            <h2>Confirmar cambio</h2>
            <dl>
              <dt>Institución</dt>
              <dd>{confirmacion.nuevo.institucion || "Sin institución"}</dd>
              <dt>Nuevo grado</dt>
              <dd>{confirmacion.nuevo.grado}</dd>
              <dt>Sección</dt>
              <dd>{confirmacion.nuevo.seccion || "Sección única"}</dd>
              <dt>Docente</dt>
              <dd>{confirmacion.nuevo.docente || "Sin docente"}</dd>
            </dl>
            <button type="button" className="pixel-primary-button success" onClick={confirmar} disabled={cargando}>
              Confirmar cambio
            </button>
          </div>
        )}
      </section>
    </section>
  );
};

export default ActualizarGradoPage;

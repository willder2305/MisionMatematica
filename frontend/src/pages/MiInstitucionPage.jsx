import React, { useEffect, useState } from "react";
import PixelAlert from "../components/ui/PixelAlert";
import PixelLoader from "../components/ui/PixelLoader";
import { obtenerOnboarding } from "../services/onboardingService";

const MiInstitucionPage = () => {
  const [perfil, setPerfil] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [mensaje, setMensaje] = useState({ tipo: "", texto: "" });

  useEffect(() => {
    const cargarPerfil = async () => {
      try {
        const respuesta = await obtenerOnboarding();
        setPerfil(respuesta.data?.perfil || null);
      } catch (error) {
        setMensaje({ tipo: "error", texto: error.message || "No fue posible cargar la institución." });
      } finally {
        setCargando(false);
      }
    };
    cargarPerfil();
  }, []);

  if (cargando) {
    return <PixelLoader text="Cargando institución..." />;
  }

  return (
    <section className="content">
      <div className="header-row">
        <div>
          <h1>Mi institución</h1>
          <p>Contexto académico asignado al docente.</p>
        </div>
      </div>

      <PixelAlert tipo={mensaje.tipo} texto={mensaje.texto} />

      <section className="panel">
        <h2>{perfil?.institucion || "Sin institución asignada"}</h2>
        <div className="institution-summary">
          {(perfil?.grados || []).map((grado) => (
            <article key={grado.id_institucion_grado || grado.id_grado}>
              <strong>{grado.nombre_grado}</strong>
              <span>{grado.secciones?.length ? grado.secciones.join(", ") : "Sección única"}</span>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
};

export default MiInstitucionPage;

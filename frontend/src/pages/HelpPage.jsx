import React from "react";
import logoMision from "../assets/pixel/logo_mision_matematica_pixel.png";
import { navegarInternamente } from "../services/navigationService";

const tutoriales = [
  {
    titulo: "Tutorial del Alumno",
    descripcion: "Aprende a utilizar Misión Matemática, acceder a las actividades y comenzar tu aventura de aprendizaje.",
    videoId: "kCkCNJFPMeM",
  },
  {
    titulo: "Tutorial del Docente",
    descripcion: "Conoce las herramientas disponibles para los docentes y aprende a utilizar las funciones educativas de la plataforma.",
    videoId: "y4ZmzUGkFp0",
  },
];

const HelpPage = () => (
  <main className="help-page">
    <header className="help-header">
      <button type="button" className="help-home-link" onClick={() => navegarInternamente("/login")}>
        Volver al inicio
      </button>
      <img className="help-logo pixel-art" src={logoMision} alt="Misión Matemática" decoding="async" />
    </header>

    <section className="help-intro" aria-labelledby="help-title">
      <p className="help-eyebrow">Recursos de aprendizaje</p>
      <h1 id="help-title">Centro de Ayuda</h1>
      <p>Aprende a utilizar Misión Matemática mediante nuestros tutoriales y manual de usuario.</p>
    </section>

    <section className="help-tutorials" aria-label="Tutoriales en video">
      {tutoriales.map((tutorial) => {
        const urlVideo = `https://www.youtube.com/watch?v=${tutorial.videoId}`;
        return (
          <article className="help-tutorial-card" key={tutorial.videoId}>
            <div className="help-card-content">
              <h2>{tutorial.titulo}</h2>
              <p>{tutorial.descripcion}</p>
            </div>
            <div className="help-video-frame">
              <iframe
                src={`https://www.youtube-nocookie.com/embed/${tutorial.videoId}?rel=0`}
                title={tutorial.titulo}
                loading="lazy"
                referrerPolicy="strict-origin-when-cross-origin"
                allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              />
            </div>
            <p className="help-video-alternative">
              ¿No se muestra el video? <a href={urlVideo} target="_blank" rel="noopener noreferrer">Ábrelo en YouTube</a>.
            </p>
          </article>
        );
      })}
    </section>

    <section className="help-manual" aria-labelledby="manual-title">
      <div>
        <p className="help-eyebrow">Consulta sin conexión</p>
        <h2 id="manual-title">Manual de Usuario</h2>
        <p>Descarga el manual de usuario de Misión Matemática para consultar las instrucciones de utilización del sistema.</p>
      </div>
      <a className="help-download-button" href="/manual/Manual_Usuario_Mision_Matematica.pdf" download="Manual_Usuario_Mision_Matematica.pdf">
        <span aria-hidden="true">↓</span>
        Descargar manual PDF
      </a>
    </section>
  </main>
);

export default HelpPage;

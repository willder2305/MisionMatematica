import React, { useEffect, useState } from "react";
import iconoGrados from "../../assets/pixel/icono_grados.png";
import iconoMenu from "../../assets/pixel/icono_menu.png";
import iconoSecciones from "../../assets/pixel/icono_secciones.png";
import logoMision from "../../assets/pixel/logo_mision_matematica_pixel.png";
import { logout, obtenerUsuarioLocal } from "../../services/authService";
import { navegarInternamente } from "../../services/navigationService";
import { obtenerOnboarding } from "../../services/onboardingService";

const navItems = [
  { href: "/juego", label: "Juego", key: "juego", mark: "J", roles: ["estudiante"] },
  { href: "/actividades", label: "Actividades", key: "actividades", mark: "A", roles: ["estudiante"], modalidades: ["grupo_educativo"] },
  { href: "/mi-personaje", label: "Mi personaje", key: "mi-personaje", mark: "P", roles: ["estudiante"] },
  { href: "/tienda", label: "Tienda", key: "tienda", mark: "T", roles: ["estudiante"] },
  { href: "/panel-estudiante", label: "Panel", key: "panel-estudiante", mark: "I", roles: ["estudiante"] },
  { href: "/admin", label: "Admin", key: "admin", mark: "A", roles: ["administrador"] },
  { href: "/mi-institucion", label: "Mi institución", key: "mi-institucion", mark: "I", roles: ["docente"] },
  { href: "/secciones", label: "Secciones", icon: iconoSecciones, key: "secciones", roles: ["docente"] },
  { href: "/admin/secciones", label: "Secciones", icon: iconoSecciones, key: "secciones", roles: ["administrador"] },
  { href: "/grados", label: "Mis grados", icon: iconoGrados, key: "grados", roles: ["docente"] },
  { href: "/admin/grados", label: "Grados", icon: iconoGrados, key: "grados", roles: ["administrador"] },
  { href: "/asignaciones", label: "Asignaciones", key: "asignaciones", mark: "A", roles: ["docente"] },
  { href: "/admin/asignaciones", label: "Asignaciones", key: "asignaciones", mark: "A", roles: ["administrador"] },
  { href: "/reportes", label: "Reportes", key: "reportes", mark: "R", roles: ["docente"] },
  { href: "/admin/reportes", label: "Reportes", key: "reportes", mark: "R", roles: ["administrador"] },
  { href: "/admin/plantillas", label: "Plantillas", key: "plantillas", mark: "T", roles: ["administrador"] },
];

/**
 * Funcion: PixelAdminLayout
 *
 * Descripcion:
 * Renderiza el layout administrativo pixel-art compartido por las vistas de secciones y grados.
 *
 * Es llamada desde:
 * src/main.jsx, envolviendo la pagina activa.
 *
 * Llama a:
 * setSidebarAbierta() para abrir o cerrar el drawer movil y usa los enlaces a /secciones y /grados.
 *
 * Parametros:
 * children con la pagina actual y activeSection para marcar la opcion activa.
 *
 * Retorna:
 * Sidebar, overlay movil, header decorativo y contenedor principal para el contenido React real.
 *
 * Manejo de errores:
 * No consume API; si ocurre un error en las paginas hijas, esas paginas conservan sus alertas visibles.
 */
const PixelAdminLayout = ({ children, activeSection }) => {
  const [sidebarAbierta, setSidebarAbierta] = useState(false);
  const [perfilEstudiante, setPerfilEstudiante] = useState(null);
  const usuario = obtenerUsuarioLocal();
  const opcionesNavegacion = usuario
    ? navItems.filter((item) => {
        if (!item.roles.includes(usuario.rol)) {
          return false;
        }
        if (usuario.rol === "estudiante" && item.modalidades) {
          return item.modalidades.includes(perfilEstudiante?.modalidad);
        }
        return true;
      })
    : [];

  const irA = (ruta) => {
    setSidebarAbierta(false);
    navegarInternamente(ruta);
  };

  /**
   * Funcion: useEffect de cierre con Escape
   *
   * Descripcion:
   * Cierra el drawer movil cuando el usuario presiona Escape.
   *
   * Es llamada desde:
   * React al montar PixelAdminLayout.
   *
   * Llama a:
   * setSidebarAbierta(false) si la tecla presionada es Escape.
   *
   * Parametros:
   * Evento keydown del navegador.
   *
   * Retorna:
   * No retorna valores; registra y limpia el listener.
   *
   * Manejo de errores:
   * Si no existe evento de teclado, no modifica el estado.
   */
  useEffect(() => {
    const cerrarConEscape = (evento) => {
      if (evento.key === "Escape") {
        setSidebarAbierta(false);
      }
    };

    window.addEventListener("keydown", cerrarConEscape);
    return () => window.removeEventListener("keydown", cerrarConEscape);
  }, []);

  useEffect(() => {
    if (usuario?.rol !== "estudiante" || !usuario.onboarding_completado) {
      setPerfilEstudiante(null);
      return;
    }
    let activo = true;
    obtenerOnboarding()
      .then((respuesta) => {
        if (activo) {
          setPerfilEstudiante(respuesta.data?.perfil || null);
        }
      })
      .catch(() => {
        if (activo) {
          setPerfilEstudiante(null);
        }
      });
    return () => {
      activo = false;
    };
  }, [usuario?.id_usuario, usuario?.rol, usuario?.onboarding_completado]);

  const rutaLogo = () => {
    if (usuario?.rol === "administrador") return "/admin";
    if (usuario?.rol === "docente") return "/mi-institucion";
    return "/juego";
  };

  const cerrarSesion = async () => {
    // Revoca el refresh token y limpia la sesion local antes de volver al login.
    await logout();
    navegarInternamente("/login", { replace: true });
  };

  return (
    <div className="pixel-shell">
      <button
        type="button"
        className="mobile-menu-button"
        onClick={() => setSidebarAbierta(true)}
        aria-label="Abrir menú"
      >
        <img className="pixel-art" src={iconoMenu} alt="Menú" />
      </button>

      <div
        className={`sidebar-overlay ${sidebarAbierta ? "visible" : ""}`}
        onClick={() => setSidebarAbierta(false)}
        role="presentation"
      />

      <aside className={`pixel-sidebar ${sidebarAbierta ? "open" : ""}`} aria-label="Navegación principal">
        <button
          type="button"
          className="sidebar-logo"
          onClick={() => irA(rutaLogo())}
        >
          <img className="pixel-art" src={logoMision} alt="Logo Misión Matemática" />
        </button>

        <nav className="sidebar-nav">
          {opcionesNavegacion.map((item) => (
            <button
              type="button"
              key={`${item.key}-${item.href}`}
              className={activeSection === item.key ? "active" : ""}
              onClick={() => irA(item.href)}
            >
              {item.icon ? (
                <img className="pixel-art" src={item.icon} alt="" aria-hidden="true" />
              ) : (
                <span className="sidebar-nav-mark" aria-hidden="true">
                  {item.mark}
                </span>
              )}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-session">
          {usuario ? (
            <>
              <span>{usuario.nombres}</span>
              <small>{usuario.rol === "administrador" ? "Administrador" : usuario.rol === "docente" ? "Docente" : "Estudiante"}</small>
              {usuario.rol === "estudiante" && perfilEstudiante?.modalidad === "grupo_educativo" && (
                <button type="button" onClick={() => irA("/actualizar-grado")}>Configuración escolar</button>
              )}
              <button type="button" onClick={cerrarSesion}>Salir</button>
            </>
          ) : (
            <button type="button" onClick={() => irA("/login")}>Ingresar</button>
          )}
        </div>
      </aside>

      <div className="pixel-main">
        <main className="page">{children}</main>
      </div>
    </div>
  );
};

export default PixelAdminLayout;



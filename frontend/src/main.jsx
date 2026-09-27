import React, { Suspense, lazy, useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import PixelAdminLayout from "./components/layout/PixelAdminLayout";
import PixelLoader from "./components/ui/PixelLoader";
import {
  guardarSesion,
  limpiarSesion,
  obtenerAccessToken,
  obtenerMe,
  obtenerRefreshToken,
  obtenerUsuarioLocal,
} from "./services/authService";
import { navegarInternamente } from "./services/navigationService";
import "./styles.css";

const AdminPage = lazy(() => import("./pages/AdminPage"));
const ActividadesPage = lazy(() => import("./pages/ActividadesPage"));
const ActualizarGradoPage = lazy(() => import("./pages/ActualizarGradoPage"));
const AsignacionesPage = lazy(() => import("./pages/AsignacionesPage"));
const GradosPage = lazy(() => import("./pages/GradosPage"));
const JuegoPage = lazy(() => import("./pages/JuegoPage"));
const MiPersonajePage = lazy(() => import("./pages/MiPersonajePage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const MiInstitucionPage = lazy(() => import("./pages/MiInstitucionPage"));
const ForgotPasswordPage = lazy(() => import("./pages/ForgotPasswordPage"));
const OnboardingPage = lazy(() => import("./pages/OnboardingPage"));
const PanelEstudiantePage = lazy(() => import("./pages/PanelEstudiantePage"));
const TiendaPage = lazy(() => import("./pages/TiendaPage"));
const PlantillasPage = lazy(() => import("./pages/PlantillasPage"));
const ReportesDocentePage = lazy(() => import("./pages/ReportesDocentePage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const SeccionesPage = lazy(() => import("./pages/SeccionesPage"));

export const RUTAS_PRINCIPALES = [
  "/login",
  "/registro",
  "/recuperar-password",
  "/onboarding",
  "/panel-estudiante",
  "/mi-personaje",
  "/tienda",
  "/actividades",
  "/actualizar-grado",
  "/mi-institucion",
  "/secciones",
  "/grados",
  "/asignaciones",
  "/reportes",
  "/admin",
  "/admin/secciones",
  "/admin/grados",
  "/admin/asignaciones",
  "/admin/reportes",
  "/admin/plantillas",
  "/juego",
];

const fallbackSesion = <PixelLoader text="Verificando sesión..." />;
const fallbackModulo = <PixelLoader text="Cargando módulo..." />;

const RUTA_POR_ROL = {
  estudiante: "/juego",
  docente: "/mi-institucion",
  administrador: "/admin",
};

const RUTAS_PUBLICAS = new Set(["/", "/login", "/registro", "/recuperar-password"]);

const normalizarRol = (rol) => {
  const valor = String(rol || "").trim().toLowerCase();
  if (valor === "admin") return "administrador";
  return valor;
};

const normalizarUsuario = (usuario) => (
  usuario ? { ...usuario, rol: normalizarRol(usuario.rol) } : null
);

const rutaInicialPorUsuario = (usuario) => {
  if (!usuario?.onboarding_completado) return "/onboarding";
  return RUTA_POR_ROL[normalizarRol(usuario.rol)] || "/login";
};

const normalizarRutaBase = (ruta) => {
  if (ruta === "/register") return "/registro";
  if (ruta === "/estudiante") return "/juego";
  if (ruta === "/docente") return "/mi-institucion";
  if (ruta === "/plantillas") return "/admin/plantillas";
  return ruta;
};

const normalizarRutaParaUsuario = (ruta, usuario) => {
  const rutaBase = normalizarRutaBase(ruta);
  if (normalizarRol(usuario?.rol) !== "administrador") return rutaBase;

  const aliasesAdmin = {
    "/secciones": "/admin/secciones",
    "/grados": "/admin/grados",
    "/asignaciones": "/admin/asignaciones",
    "/reportes": "/admin/reportes",
  };
  return aliasesAdmin[rutaBase] || rutaBase;
};

const redirigir = (ruta) => {
  navegarInternamente(ruta, { replace: true });
};

const rutasPrivadas = {
  "/admin": { componente: AdminPage, activeSection: "admin", roles: ["administrador"] },
  "/admin/secciones": { componente: SeccionesPage, activeSection: "secciones", roles: ["administrador"] },
  "/admin/grados": { componente: GradosPage, activeSection: "grados", roles: ["administrador"] },
  "/admin/asignaciones": { componente: AsignacionesPage, activeSection: "asignaciones", roles: ["administrador"] },
  "/admin/reportes": { componente: ReportesDocentePage, activeSection: "reportes", roles: ["administrador"] },
  "/admin/plantillas": { componente: PlantillasPage, activeSection: "plantillas", roles: ["administrador"] },
  "/mi-institucion": { componente: MiInstitucionPage, activeSection: "mi-institucion", roles: ["docente"] },
  "/secciones": { componente: SeccionesPage, activeSection: "secciones", roles: ["docente"] },
  "/grados": { componente: GradosPage, activeSection: "grados", roles: ["docente"] },
  "/asignaciones": { componente: AsignacionesPage, activeSection: "asignaciones", roles: ["docente"] },
  "/reportes": { componente: ReportesDocentePage, activeSection: "reportes", roles: ["docente"] },
  "/panel-estudiante": { componente: PanelEstudiantePage, activeSection: "panel-estudiante", roles: ["estudiante"] },
  "/mi-personaje": { componente: MiPersonajePage, activeSection: "mi-personaje", roles: ["estudiante"] },
  "/tienda": { componente: TiendaPage, activeSection: "tienda", roles: ["estudiante"] },
  "/actividades": { componente: ActividadesPage, activeSection: "actividades", roles: ["estudiante"] },
  "/actualizar-grado": { componente: ActualizarGradoPage, activeSection: "actualizar-grado", roles: ["estudiante"] },
  "/juego": { componente: JuegoPage, activeSection: "juego", roles: ["estudiante"] },
};

class ModuleErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidUpdate(prevProps) {
    if (prevProps.resetKey !== this.props.resetKey && this.state.hasError) {
      this.setState({ hasError: false });
    }
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <section className="content">
        <div className="panel">
          <h1>No fue posible cargar este módulo.</h1>
          <p>Intenta cargar la pantalla nuevamente.</p>
          <button type="button" className="pixel-primary-button" onClick={() => this.setState({ hasError: false })}>
            Reintentar
          </button>
        </div>
      </section>
    );
  }
}

const NotFoundPage = ({ usuario }) => (
  <section className="content">
    <div className="header-row">
      <div>
        <h1>Ruta no encontrada</h1>
        <p>La pantalla solicitada no existe en Misión Matemática.</p>
      </div>
      <button
        type="button"
        className="pixel-primary-button success"
        onClick={() => redirigir(usuario ? rutaInicialPorUsuario(usuario) : "/login")}
      >
        Volver al inicio
      </button>
    </div>
  </section>
);

const App = () => {
  const [rutaNavegacion, setRutaNavegacion] = useState(window.location.pathname);
  const [estadoSesion, setEstadoSesion] = useState({
    loading: true,
    usuario: normalizarUsuario(obtenerUsuarioLocal()),
  });

  useEffect(() => {
    const sincronizarRuta = () => setRutaNavegacion(window.location.pathname);
    const actualizarUsuario = () => {
      setEstadoSesion((actual) => ({
        ...actual,
        usuario: normalizarUsuario(obtenerUsuarioLocal()),
      }));
    };
    const invalidarSesion = () => {
      setEstadoSesion({ loading: false, usuario: null });
    };

    window.addEventListener("popstate", sincronizarRuta);
    window.addEventListener("mm:navigation", sincronizarRuta);
    window.addEventListener("mm:auth-updated", actualizarUsuario);
    window.addEventListener("mm:auth-invalid", invalidarSesion);
    return () => {
      window.removeEventListener("popstate", sincronizarRuta);
      window.removeEventListener("mm:navigation", sincronizarRuta);
      window.removeEventListener("mm:auth-updated", actualizarUsuario);
      window.removeEventListener("mm:auth-invalid", invalidarSesion);
    };
  }, []);

  useEffect(() => {
    let activo = true;
    const tieneCredencial = Boolean(obtenerAccessToken() || obtenerRefreshToken());

    if (!tieneCredencial) {
      limpiarSesion();
      setEstadoSesion({ loading: false, usuario: null });
      return undefined;
    }

    obtenerMe()
      .then((respuesta) => {
        if (!activo) return;
        const usuarioActual = normalizarUsuario(respuesta.data?.usuario);
        if (!usuarioActual) {
          limpiarSesion();
          setEstadoSesion({ loading: false, usuario: null });
          return;
        }
        guardarSesion({ usuario: usuarioActual });
        setEstadoSesion({ loading: false, usuario: usuarioActual });
      })
      .catch((error) => {
        if (!activo) return;
        const status = error.response?.status;
        if (status === 401) {
          limpiarSesion();
          setEstadoSesion({ loading: false, usuario: null });
          return;
        }
        setEstadoSesion((actual) => ({ loading: false, usuario: actual.usuario }));
      });

    return () => {
      activo = false;
    };
  }, []);

  useEffect(() => {
    if (estadoSesion.loading) return;
    const rutaNormalizada = normalizarRutaParaUsuario(rutaNavegacion, estadoSesion.usuario);
    if (rutaNormalizada === rutaNavegacion) return;
    window.history.replaceState({}, "", rutaNormalizada);
    setRutaNavegacion(rutaNormalizada);
  }, [estadoSesion.loading, estadoSesion.usuario, rutaNavegacion]);

  if (estadoSesion.loading) {
    return fallbackSesion;
  }

  const usuario = estadoSesion.usuario;
  const rutaActual = normalizarRutaParaUsuario(rutaNavegacion, usuario);

  if (rutaActual !== rutaNavegacion) {
    return fallbackModulo;
  }

  if (RUTAS_PUBLICAS.has(rutaActual)) {
    if (usuario) {
      redirigir(rutaInicialPorUsuario(usuario));
      return fallbackModulo;
    }
    return (
      <Suspense fallback={fallbackModulo}>
        {rutaActual === "/registro"
          ? <RegisterPage />
          : rutaActual === "/recuperar-password"
            ? <ForgotPasswordPage />
            : <LoginPage />}
      </Suspense>
    );
  }

  if (!usuario) {
    redirigir("/login");
    return fallbackSesion;
  }

  if (rutaActual === "/onboarding") {
    if (usuario.onboarding_completado) {
      redirigir(rutaInicialPorUsuario(usuario));
      return fallbackModulo;
    }
    return (
      <Suspense fallback={fallbackModulo}>
        <OnboardingPage />
      </Suspense>
    );
  }

  if (!usuario.onboarding_completado) {
    redirigir("/onboarding");
    return fallbackModulo;
  }

  const ruta = rutasPrivadas[rutaActual];
  if (!ruta) {
    return (
      <PixelAdminLayout activeSection="">
        <NotFoundPage usuario={usuario} />
      </PixelAdminLayout>
    );
  }

  if (!ruta.roles.includes(normalizarRol(usuario.rol))) {
    redirigir(rutaInicialPorUsuario(usuario));
    return fallbackModulo;
  }

  const Page = ruta.componente;

  return (
    <PixelAdminLayout activeSection={ruta.activeSection}>
      <ModuleErrorBoundary resetKey={rutaActual}>
        <Suspense fallback={fallbackModulo}>
          <Page />
        </Suspense>
      </ModuleErrorBoundary>
    </PixelAdminLayout>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

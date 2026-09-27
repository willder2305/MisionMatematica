import api from "./apiClient";

export const obtenerOnboarding = async () => {
  const response = await api.get("/onboarding");
  return response.data;
};

export const obtenerPersonajesIniciales = async () => {
  const response = await api.get("/onboarding/personajes-iniciales");
  return response.data;
};

export const completarOnboarding = async (datos) => {
  const response = await api.post("/onboarding", datos);
  return response.data;
};

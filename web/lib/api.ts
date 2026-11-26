export type Overview = { status: string; locations_monitored: number; forecast_points: number; observation_points: number; latest_retrieval_at: string | null; data_source: string };
export type Location = { name: string; latitude: number; longitude: number; timezone_name: string | null; latest_forecast_at: string | null; forecast_points: number };
export type ForecastPoint = { valid_at: string; issued_at: string; source: string; temperature_c: number | null; precipitation_mm: number | null; precipitation_probability_pct: number | null; relative_humidity_pct: number | null; wind_speed_kmh: number | null; surface_pressure_hpa: number | null };
const API_ROOT = process.env.NEXT_PUBLIC_EARTH_API_URL || "http://localhost:8000/api/v1";
const API_URL = API_ROOT.endsWith("/") ? API_ROOT.slice(0, -1) : API_ROOT;
async function get<T>(path: string): Promise<T> { const response = await fetch(API_URL + path, { cache: "no-store" }); if (!response.ok) throw new Error("EARTH API returned " + response.status); return response.json() as Promise<T>; }
export const api = { health: () => get<{status:string;service:string;timestamp:string}>("/health"), overview: () => get<Overview>("/overview"), locations: () => get<Location[]>("/locations"), forecast: (location:string,hours=48) => get<ForecastPoint[]>("/forecast?location="+encodeURIComponent(location)+"&hours="+hours) };

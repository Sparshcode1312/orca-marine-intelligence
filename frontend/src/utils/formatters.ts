import type {
  AgentName,
  LanguageCode,
  Recommendation,
  RiskLevel,
  VesselType,
} from "../types/orca";


const languageLocales: Record<LanguageCode, string> = {
  en: "en-IN",
  hi: "hi-IN",
  or: "or-IN",
};


const recommendationLabels: Record<
  Recommendation,
  string
> = {
  proceed: "Safe to proceed",
  proceed_with_caution: "Proceed with caution",
  do_not_proceed: "Do not proceed",
  insufficient_data: "Insufficient data",
};


const riskLabels: Record<RiskLevel, string> = {
  low: "Low risk",
  moderate: "Moderate risk",
  high: "High risk",
  severe: "Severe risk",
  unknown: "Unknown risk",
};


const vesselLabels: Record<VesselType, string> = {
  traditional: "Traditional boat",
  small_motorized: "Small motorized boat",
  trawler: "Trawler",
};


const agentLabels: Record<AgentName, string> = {
  planner: "Planner",
  weather: "Weather",
  ocean: "Ocean",
  pfz: "Fishing Zone",
  gis: "Route & GIS",
  safety: "Safety",
};


export function formatRecommendation(
  recommendation: Recommendation,
): string {
  return recommendationLabels[recommendation];
}


export function formatRiskLevel(
  riskLevel: RiskLevel,
): string {
  return riskLabels[riskLevel];
}


export function formatVesselType(
  vesselType: VesselType,
): string {
  return vesselLabels[vesselType];
}


export function formatAgentName(
  agentName: AgentName,
): string {
  return agentLabels[agentName];
}


export function formatDistance(
  distanceKm: number,
): string {
  return `${distanceKm.toFixed(1)} km`;
}


export function formatDuration(
  totalMinutes: number,
): string {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0) {
    return `${minutes} min`;
  }

  if (minutes === 0) {
    return `${hours} hr`;
  }

  return `${hours} hr ${minutes} min`;
}


export function formatConfidence(
  confidence: number,
): string {
  return `${Math.round(confidence * 100)}%`;
}


export function formatScore(
  score: number,
): string {
  return `${Math.round(score)}/100`;
}


export function formatDateTime(
  value: string,
  language: LanguageCode = "en",
): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unavailable";
  }

  return new Intl.DateTimeFormat(
    languageLocales[language],
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


export function formatFreshness(
  minutes: number,
): string {
  if (minutes < 1) {
    return "Updated just now";
  }

  if (minutes < 60) {
    return `Updated ${minutes} min ago`;
  }

  const hours = Math.floor(minutes / 60);

  if (hours < 24) {
    return `Updated ${hours} hr ago`;
  }

  const days = Math.floor(hours / 24);

  return `Updated ${days} day${days === 1 ? "" : "s"} ago`;
}


export function toDateTimeLocalValue(
  date: Date,
): string {
  const timezoneOffset = date.getTimezoneOffset() * 60_000;

  return new Date(date.getTime() - timezoneOffset)
    .toISOString()
    .slice(0, 16);
}


export function dateTimeLocalToIso(
  value: string,
): string {
  return new Date(value).toISOString();
}
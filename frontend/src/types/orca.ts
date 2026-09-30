export type LanguageCode = "en" | "hi" | "or";

export type VesselType =
  | "traditional"
  | "small_motorized"
  | "trawler";

export type Recommendation =
  | "proceed"
  | "proceed_with_caution"
  | "do_not_proceed"
  | "insufficient_data";

export type RiskLevel =
  | "low"
  | "moderate"
  | "high"
  | "severe"
  | "unknown";

export type SourceType =
  | "advisory"
  | "forecast"
  | "observation"
  | "satellite"
  | "geospatial"
  | "safety_rule";

export type AgentName =
  | "planner"
  | "weather"
  | "ocean"
  | "pfz"
  | "gis"
  | "safety";

export type AgentStatus =
  | "succeeded"
  | "partial"
  | "failed"
  | "skipped";

export interface GeoPoint {
  latitude: number;
  longitude: number;
}

export interface TripAnalysisRequest {
  query: string;
  language: LanguageCode;
  origin: GeoPoint;
  planned_departure: string;
  max_distance_km: number;
  vessel_type: VesselType;
  crew_count: number;
  include_explanation: boolean;
}

export interface EvidenceItem {
  source_name: string;
  source_type: SourceType;
  summary: string;
  observed_at: string;
  retrieved_at: string;
  freshness_minutes: number;
  confidence: number;
  reference_url: string | null;
}

export interface RiskFactor {
  code: string;
  label: string;
  level: RiskLevel;
  score: number;
  explanation: string;
}

export interface AgentExecution {
  agent: AgentName;
  status: AgentStatus;
  started_at: string;
  completed_at: string;
  evidence_count: number;
  error_code: string | null;
}

export interface FishingZoneRecommendation {
  zone_id: string;
  name: string;
  center: GeoPoint;
  suitability_score: number;
  distance_km: number;
  recommended_from: string;
  recommended_until: string;
}

export interface RouteRecommendation {
  distance_km: number;
  estimated_duration_minutes: number;
  waypoints: GeoPoint[];
  advisory: string;
}

export interface IntelligenceDecision {
  decision_id: string;
  request_id: string;
  generated_at: string;

  recommendation: Recommendation;
  risk_level: RiskLevel;

  safety_score: number;
  confidence: number;

  summary: string;
  reasons: string[];
  alerts: string[];

  risk_factors: RiskFactor[];
  evidence: EvidenceItem[];
  agent_executions: AgentExecution[];

  recommended_zone: FishingZoneRecommendation | null;
  recommended_route: RouteRecommendation | null;

  prototype_data: boolean;
  human_verification_required: boolean;
}

export interface ApiValidationError {
  loc: Array<string | number>;
  msg: string;
  type: string;
}

export interface ApiErrorResponse {
  detail: string | ApiValidationError[];
}
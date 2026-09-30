import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Compass,
  Fish,
  Gauge,
  MapPin,
  Navigation,
  Route,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

import type {
  IntelligenceDecision,
  LanguageCode,
} from "../../types/orca";

import {
  formatConfidence,
  formatDateTime,
  formatDistance,
  formatDuration,
  formatRecommendation,
  formatRiskLevel,
  formatScore,
} from "../../utils/formatters";

import { RouteMap } from "../map/RouteMap";


interface DecisionDashboardProps {
  decision: IntelligenceDecision;
  language: LanguageCode;
}


export function DecisionDashboard({
  decision,
  language,
}: DecisionDashboardProps) {
  const zone = decision.recommended_zone;
  const route = decision.recommended_route;

  return (
    <div className="decision-dashboard">
      <section
        className={`decision-hero decision-hero--${decision.recommendation}`}
      >
        <div className="decision-hero__icon">
          <ShieldCheck size={28} />
        </div>

        <div>
          <span>ORCA recommendation</span>

          <h3>
            {formatRecommendation(decision.recommendation)}
          </h3>
        </div>
      </section>

      <section className="decision-metrics">
        <article>
          <Gauge size={18} />

          <div>
            <span>Safety score</span>
            <strong>
              {formatScore(decision.safety_score)}
            </strong>
          </div>
        </article>

        <article>
          <AlertTriangle size={18} />

          <div>
            <span>Risk level</span>
            <strong>
              {formatRiskLevel(decision.risk_level)}
            </strong>
          </div>
        </article>

        <article>
          <Target size={18} />

          <div>
            <span>Confidence</span>
            <strong>
              {formatConfidence(decision.confidence)}
            </strong>
          </div>
        </article>
      </section>

      <section className="decision-summary">
        <div className="subsection-heading">
          <Sparkles size={18} />
          <h3>Intelligence summary</h3>
        </div>

        <p>{decision.summary}</p>
      </section>

      {decision.alerts.length > 0 && (
        <section className="decision-alerts">
          <div className="subsection-heading">
            <AlertTriangle size={18} />
            <h3>Active alerts</h3>
          </div>

          <ul>
            {decision.alerts.map((alert) => (
              <li key={alert}>{alert}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="decision-reasons">
        <div className="subsection-heading">
          <CheckCircle2 size={18} />
          <h3>Why ORCA made this decision</h3>
        </div>

        <ul>
          {decision.reasons.map((reason, index) => (
            <li key={`${index}-${reason}`}>
              <span>{index + 1}</span>
              <p>{reason}</p>
            </li>
          ))}
        </ul>
      </section>

      {(zone || route) && (
        <section className="journey-grid">
          {zone && (
            <article className="journey-card">
              <div className="journey-card__heading">
                <span>
                  <Fish size={20} />
                </span>

                <div>
                  <small>Recommended fishing zone</small>
                  <h3>{zone.name}</h3>
                </div>
              </div>

              <div className="journey-card__metrics">
                <div>
                  <span>Suitability</span>
                  <strong>
                    {zone.suitability_score}/100
                  </strong>
                </div>

                <div>
                  <span>Distance</span>
                  <strong>
                    {formatDistance(zone.distance_km)}
                  </strong>
                </div>
              </div>

              <div className="coordinate-row">
                <MapPin size={15} />

                <span>
                  {zone.center.latitude.toFixed(4)},{" "}
                  {zone.center.longitude.toFixed(4)}
                </span>
              </div>

              <div className="validity-row">
                <Clock3 size={15} />

                <span>
                  Valid until{" "}
                  {formatDateTime(
                    zone.recommended_until,
                    language,
                  )}
                </span>
              </div>
            </article>
          )}

          {route && (
            <article className="journey-card">
              <div className="journey-card__heading">
                <span>
                  <Route size={20} />
                </span>

                <div>
                  <small>Recommended route</small>
                  <h3>Safer navigation path</h3>
                </div>
              </div>

              <div className="journey-card__metrics">
                <div>
                  <span>Distance</span>
                  <strong>
                    {formatDistance(route.distance_km)}
                  </strong>
                </div>

                <div>
                  <span>Estimated time</span>
                  <strong>
                    {formatDuration(
                      route.estimated_duration_minutes,
                    )}
                  </strong>
                </div>
              </div>

              <div className="coordinate-row">
                <Compass size={15} />

                <span>
                  {route.waypoints.length} route waypoints
                </span>
              </div>

              <p className="route-advisory">
                <Navigation size={15} />
                <span>{route.advisory}</span>
              </p>
            </article>
          )}
        </section>
      )}

      {zone && route && (
  <RouteMap
    zone={zone}
    route={route}
  />
)}

      <section className="human-review">
        <AlertTriangle size={18} />

        <div>
          <strong>Human verification required</strong>

          <p>
            Confirm this prototype guidance using official
            maritime advisories before departure.
          </p>
        </div>
      </section>

      <footer className="decision-footer">
        <span>
          Decision ID: {decision.decision_id.slice(0, 8)}
        </span>

        <span>
          Generated{" "}
          {formatDateTime(decision.generated_at, language)}
        </span>
      </footer>
    </div>
  );
}
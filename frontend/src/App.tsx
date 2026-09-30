import { useState } from "react";

import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  LoaderCircle,
  MapPinned,
  Route,
  Waves,
} from "lucide-react";

import "./App.css";

import { DecisionDashboard } from "./components/decision/DecisionDashboard";
import { AppHeader } from "./components/layout/AppHeader";
import { TripPlanner } from "./components/trip/TripPlanner";
import { useTripAnalysis } from "./hooks/useTripAnalysis";
import type { LanguageCode } from "./types/orca";


function App() {
  const [language, setLanguage] =
    useState<LanguageCode>("en");

  const {
    decision,
    error,
    isLoading,
    analyze,
  } = useTripAnalysis();

  return (
    <div className="app" id="top">
      <AppHeader
        language={language}
        onLanguageChange={setLanguage}
      />

      <main className="app-main">
        <section className="hero">
          <div className="hero__content">
            <div className="eyebrow">
              <BrainCircuit
                size={16}
                aria-hidden="true"
              />

              Multi-agent marine intelligence
            </div>

            <h1>
              Safer decisions before
              <span> every journey at sea.</span>
            </h1>

            <p>
              ORCA combines weather, ocean, fishing-zone,
              route and vessel intelligence into one clear,
              evidence-backed recommendation.
            </p>

            <div className="hero__capabilities">
              <span>
                <Waves
                  size={17}
                  aria-hidden="true"
                />

                Ocean conditions
              </span>

              <span>
                <MapPinned
                  size={17}
                  aria-hidden="true"
                />

                Fishing zones
              </span>

              <span>
                <Route
                  size={17}
                  aria-hidden="true"
                />

                Safe routing
              </span>
            </div>
          </div>

          <div
            className="hero__visual"
            aria-label="ORCA intelligence network"
          >
            <div className="radar">
              <div className="radar__ring radar__ring--one" />
              <div className="radar__ring radar__ring--two" />
              <div className="radar__ring radar__ring--three" />

              <div className="radar__sweep" />

              <div className="radar__center">
                <BrainCircuit
                  size={32}
                  aria-hidden="true"
                />

                <strong>ORCA</strong>
              </div>

              <span className="radar__point radar__point--one" />
              <span className="radar__point radar__point--two" />
              <span className="radar__point radar__point--three" />
            </div>
          </div>
        </section>

        <section className="workspace">
          <article className="workspace-card">
            <div className="section-heading">
              <span>01</span>

              <div>
                <h2>Plan your journey</h2>

                <p>
                  Tell ORCA where and how you plan to travel.
                </p>
              </div>
            </div>

            <TripPlanner
              language={language}
              isLoading={isLoading}
              onSubmit={analyze}
            />
          </article>

          <article className="workspace-card">
            <div className="section-heading">
              <span>02</span>

              <div>
                <h2>Intelligence decision</h2>

                <p>
                  Safety, route and evidence in one view.
                </p>
              </div>
            </div>

            {isLoading && (
              <div
                className="analysis-state"
                role="status"
                aria-live="polite"
              >
                <div className="analysis-state__icon">
                  <LoaderCircle
                    className="spin"
                    size={34}
                    aria-hidden="true"
                  />
                </div>

                <h3>ORCA agents are collaborating</h3>

                <p>
                  Weather, ocean, fishing-zone, GIS and safety
                  agents are building your decision.
                </p>

                <div className="agent-loading-list">
                  {[
                    "Weather",
                    "Ocean",
                    "Fishing zone",
                    "Route & GIS",
                    "Safety",
                  ].map((agent) => (
                    <span key={agent}>
                      <CheckCircle2
                        size={15}
                        aria-hidden="true"
                      />

                      {agent}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {!isLoading && error && (
              <div
                className="error-state"
                role="alert"
              >
                <AlertTriangle
                  size={32}
                  aria-hidden="true"
                />

                <h3>Analysis could not be completed</h3>

                <p>{error}</p>
              </div>
            )}

            {!isLoading && !error && decision && (
              <DecisionDashboard
                decision={decision}
                language={language}
              />
            )}

            {!isLoading && !error && !decision && (
              <div className="placeholder-content">
                Submit your trip details to activate ORCA’s
                specialist agents.
              </div>
            )}
          </article>
        </section>
      </main>
    </div>
  );
}


export default App;
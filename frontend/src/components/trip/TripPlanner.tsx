import {
  useState,
  type FormEvent,
} from "react";

import {
  CalendarClock,
  Crosshair,
  LoaderCircle,
  MapPin,
  Navigation,
  Ruler,
  Ship,
  Users,
} from "lucide-react";

import type {
  LanguageCode,
  TripAnalysisRequest,
  VesselType,
} from "../../types/orca";

import {
  dateTimeLocalToIso,
  toDateTimeLocalValue,
} from "../../utils/formatters";


interface TripPlannerProps {
  language: LanguageCode;
  isLoading: boolean;
  onSubmit: (
    request: TripAnalysisRequest,
  ) => Promise<unknown> | unknown;
}


export function TripPlanner({
  language,
  isLoading,
  onSubmit,
}: TripPlannerProps) {
  const [query, setQuery] = useState(
    "Find the best fishing zone and check whether my trip is safe.",
  );

  const [latitude, setLatitude] = useState("19.8135");
  const [longitude, setLongitude] = useState("85.8312");

  const [departure, setDeparture] = useState(
    toDateTimeLocalValue(
      new Date(Date.now() + 3 * 60 * 60 * 1000),
    ),
  );

  const [maxDistance, setMaxDistance] = useState("50");

  const [vesselType, setVesselType] =
    useState<VesselType>("small_motorized");

  const [crewCount, setCrewCount] = useState("4");

  const [locationMessage, setLocationMessage] =
    useState<string | null>(null);


  const minimumDeparture = toDateTimeLocalValue(
    new Date(Date.now() + 15 * 60 * 1000),
  );

  const maximumDeparture = toDateTimeLocalValue(
    new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
  );


  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationMessage(
        "Location access is not supported by this browser.",
      );

      return;
    }

    setLocationMessage("Requesting location permission…");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(
          position.coords.latitude.toFixed(6),
        );

        setLongitude(
          position.coords.longitude.toFixed(6),
        );

        setLocationMessage("Current location added.");
      },
      () => {
        setLocationMessage(
          "Location access was unavailable. Enter coordinates manually.",
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 10_000,
        maximumAge: 60_000,
      },
    );
  };


  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    const request: TripAnalysisRequest = {
      query: query.trim(),
      language,
      origin: {
        latitude: Number(latitude),
        longitude: Number(longitude),
      },
      planned_departure: dateTimeLocalToIso(departure),
      max_distance_km: Number(maxDistance),
      vessel_type: vesselType,
      crew_count: Number(crewCount),
      include_explanation: true,
    };

    await onSubmit(request);
  };


  return (
    <form
      className="trip-form"
      onSubmit={handleSubmit}
    >
      <div className="form-field form-field--full">
        <label htmlFor="trip-query">
          What do you want ORCA to assess?
        </label>

        <div className="textarea-control">
          <Navigation size={18} aria-hidden="true" />

          <textarea
            id="trip-query"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
            }}
            minLength={5}
            maxLength={500}
            rows={3}
            required
            disabled={isLoading}
          />
        </div>

        <span className="field-hint">
          Ask about safety, fishing zones, weather or routing.
        </span>
      </div>

      <div className="form-section-label">
        <MapPin size={16} aria-hidden="true" />
        Starting location
      </div>

      <div className="coordinate-grid">
        <div className="form-field">
          <label htmlFor="latitude">Latitude</label>

          <input
            id="latitude"
            type="number"
            value={latitude}
            onChange={(event) => {
              setLatitude(event.target.value);
            }}
            min="-90"
            max="90"
            step="0.000001"
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-field">
          <label htmlFor="longitude">Longitude</label>

          <input
            id="longitude"
            type="number"
            value={longitude}
            onChange={(event) => {
              setLongitude(event.target.value);
            }}
            min="-180"
            max="180"
            step="0.000001"
            required
            disabled={isLoading}
          />
        </div>
      </div>

      <button
        className="location-button"
        type="button"
        onClick={useCurrentLocation}
        disabled={isLoading}
      >
        <Crosshair size={16} />
        Use my current location
      </button>

      {locationMessage && (
        <p
          className="location-message"
          role="status"
        >
          {locationMessage}
        </p>
      )}

      <div className="form-field form-field--full">
        <label htmlFor="departure">
          <CalendarClock size={16} aria-hidden="true" />
          Planned departure
        </label>

        <input
          id="departure"
          type="datetime-local"
          value={departure}
          onChange={(event) => {
            setDeparture(event.target.value);
          }}
          min={minimumDeparture}
          max={maximumDeparture}
          required
          disabled={isLoading}
        />
      </div>

      <div className="form-grid">
        <div className="form-field">
          <label htmlFor="vessel-type">
            <Ship size={16} aria-hidden="true" />
            Vessel
          </label>

          <select
            id="vessel-type"
            value={vesselType}
            onChange={(event) => {
              setVesselType(
                event.target.value as VesselType,
              );
            }}
            disabled={isLoading}
          >
            <option value="traditional">
              Traditional boat
            </option>

            <option value="small_motorized">
              Small motorized boat
            </option>

            <option value="trawler">
              Trawler
            </option>
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="crew-count">
            <Users size={16} aria-hidden="true" />
            Crew
          </label>

          <input
            id="crew-count"
            type="number"
            value={crewCount}
            onChange={(event) => {
              setCrewCount(event.target.value);
            }}
            min="1"
            max="50"
            step="1"
            required
            disabled={isLoading}
          />
        </div>
      </div>

      <div className="form-field form-field--full">
        <label htmlFor="max-distance">
          <Ruler size={16} aria-hidden="true" />
          Maximum travel distance
        </label>

        <div className="range-heading">
          <span>1 km</span>
          <strong>{maxDistance} km</strong>
          <span>200 km</span>
        </div>

        <input
          id="max-distance"
          type="range"
          value={maxDistance}
          onChange={(event) => {
            setMaxDistance(event.target.value);
          }}
          min="1"
          max="200"
          step="1"
          disabled={isLoading}
        />
      </div>

      <button
        className="analyze-button"
        type="submit"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <LoaderCircle
              className="spin"
              size={19}
            />
            Agents are analyzing…
          </>
        ) : (
          <>
            <Navigation size={19} />
            Analyze my journey
          </>
        )}
      </button>

      <p className="prototype-notice">
        Prototype guidance only. Confirm critical decisions with
        official local maritime authorities.
      </p>
    </form>
  );
}
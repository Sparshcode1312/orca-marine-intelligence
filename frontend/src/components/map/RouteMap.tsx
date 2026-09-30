import { useEffect, useMemo } from "react";

import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import { latLngBounds, type LatLngTuple } from "leaflet";

import {
  Fish,
  MapPin,
  Navigation,
} from "lucide-react";

import type {
  FishingZoneRecommendation,
  RouteRecommendation,
} from "../../types/orca";

import {
  formatDistance,
  formatDuration,
} from "../../utils/formatters";


interface RouteMapProps {
  zone: FishingZoneRecommendation;
  route: RouteRecommendation;
}


interface MapBoundsControllerProps {
  positions: LatLngTuple[];
}


function MapBoundsController({
  positions,
}: MapBoundsControllerProps) {
  const map = useMap();

  useEffect(() => {
    if (positions.length < 2) {
      return;
    }

    map.fitBounds(
      latLngBounds(positions),
      {
        padding: [42, 42],
        maxZoom: 12,
      },
    );
  }, [map, positions]);

  return null;
}


export function RouteMap({
  zone,
  route,
}: RouteMapProps) {
  const routePositions = useMemo<LatLngTuple[]>(
    () =>
      route.waypoints.map((waypoint) => [
        waypoint.latitude,
        waypoint.longitude,
      ]),
    [route.waypoints],
  );

  const zonePosition = useMemo<LatLngTuple>(
    () => [
      zone.center.latitude,
      zone.center.longitude,
    ],
    [zone.center.latitude, zone.center.longitude],
  );

  const allPositions = useMemo(
    () => [...routePositions, zonePosition],
    [routePositions, zonePosition],
  );

  const initialPosition =
    routePositions[0] ?? zonePosition;

  return (
    <section className="route-map-section">
      <div className="route-map-heading">
        <div>
          <span className="route-map-heading__icon">
            <Navigation size={19} />
          </span>

          <div>
            <h3>Marine route intelligence</h3>

            <p>
              Interactive prototype route to the recommended zone.
            </p>
          </div>
        </div>

        <div className="route-map-summary">
          <span>{formatDistance(route.distance_km)}</span>

          <span>
            {formatDuration(
              route.estimated_duration_minutes,
            )}
          </span>
        </div>
      </div>

      <div className="route-map">
        <MapContainer
          center={initialPosition}
          zoom={9}
          scrollWheelZoom
          className="route-map__container"
        >
          <TileLayer
            attribution={
              '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapBoundsController positions={allPositions} />

          <Polyline
            positions={routePositions}
            pathOptions={{
              color: "#31d3c5",
              weight: 4,
              opacity: 0.9,
              dashArray: "9 7",
            }}
          />

          {routePositions.map((position, index) => {
            const isOrigin = index === 0;
            const isLast =
              index === routePositions.length - 1;

            return (
              <CircleMarker
                key={`${position[0]}-${position[1]}-${index}`}
                center={position}
                radius={isOrigin || isLast ? 9 : 5}
                pathOptions={{
                  color: isOrigin
                    ? "#58a6ff"
                    : "#8af1e7",
                  fillColor: isOrigin
                    ? "#58a6ff"
                    : "#31d3c5",
                  fillOpacity: 0.95,
                  weight: 3,
                }}
              >
                <Popup>
                  <strong>
                    {isOrigin
                      ? "Starting point"
                      : isLast
                        ? "Final route waypoint"
                        : `Waypoint ${index + 1}`}
                  </strong>

                  <br />

                  {position[0].toFixed(4)},{" "}
                  {position[1].toFixed(4)}
                </Popup>
              </CircleMarker>
            );
          })}

          <CircleMarker
            center={zonePosition}
            radius={12}
            pathOptions={{
              color: "#f4c95d",
              fillColor: "#f4c95d",
              fillOpacity: 0.95,
              weight: 4,
            }}
          >
            <Popup>
              <strong>{zone.name}</strong>

              <br />

              Suitability: {zone.suitability_score}/100

              <br />

              Distance: {formatDistance(zone.distance_km)}
            </Popup>
          </CircleMarker>
        </MapContainer>
      </div>

      <div className="route-map-legend">
        <span>
          <i className="map-dot map-dot--origin" />
          <MapPin size={14} />
          Starting point
        </span>

        <span>
          <i className="map-line" />
          <Navigation size={14} />
          Recommended route
        </span>

        <span>
          <i className="map-dot map-dot--zone" />
          <Fish size={14} />
          Fishing zone
        </span>
      </div>

      <p className="map-disclaimer">
        The displayed route uses prototype geospatial data and
        must not replace official marine navigation systems.
      </p>
    </section>
  );
}
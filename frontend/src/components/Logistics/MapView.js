import React, { useMemo } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix default marker icons path in many bundlers
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({ iconUrl, iconRetinaUrl, shadowUrl, iconSize: [25,41], iconAnchor: [12,41] });
L.Marker.prototype.options.icon = DefaultIcon;

const MapView = ({ geometry = [], points = [], bbox = null, height = 420 }) => {
  const center = useMemo(() => {
    if (geometry && geometry.length) return [geometry[0][1], geometry[0][0]];
    if (points && points.length && points[0].lat && points[0].lon) return [points[0].lat, points[0].lon];
    return [55.751244, 37.618423]; // Moscow center
  }, [geometry, points]);

  const polyline = useMemo(() => geometry.map(([lon, lat]) => [lat, lon]), [geometry]);

  return (
    <div className="rounded-xl overflow-hidden border">
      <MapContainer center={center} zoom={11} style={{ height }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {polyline.length > 0 && (
          <Polyline positions={polyline} pathOptions={{ color: '#0ea5e9', weight: 5, opacity: 0.85 }} />
        )}
        {points.map((p, i) => (
          p.lat && p.lon ? (
            <Marker key={i} position={[p.lat, p.lon]}>
              <Popup>
                Точка {i + 1}
                {p.address ? <div className="text-xs text-gray-600">{p.address}</div> : null}
              </Popup>
            </Marker>
          ) : null
        ))}
      </MapContainer>
    </div>
  );
};

export default MapView;

import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function GeoMap({ siteData }) {
  if (!siteData || siteData.length === 0) return null;

  return (
    <div className="h-96 w-full border rounded">
      <MapContainer center={[siteData[0].latitude, siteData[0].longitude]} zoom={6} className="h-full w-full">
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {siteData.map((site, idx) => (
          <Marker key={idx} position={[site.latitude, site.longitude]}>
            <Popup>
              <strong>{site.site}</strong><br />
              Chl-a: {site.chlorophyll_a} µg/L<br />
              Bloom Prob: {site.bloom_probability}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
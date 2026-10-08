import { useEffect, useRef, useState } from "react";
import { loadGooglePlaces } from "../services/googlePlaces";

export default function AddressAutocomplete({
  id,
  value,
  onChange,
  onPlaceSelected,
  onPlaceCleared,
}) {
  const inputRef = useRef(null);
  const selectedTextsRef = useRef(new Set());
  const applyingSelectionRef = useRef(false);
  const [mapsError, setMapsError] = useState("");

  useEffect(() => {
    let cancelled = false;
    let listener;
    let autocomplete;

    loadGooglePlaces()
      .then(() => {
        if (cancelled || !inputRef.current) {
          return;
        }
        if (!window.google?.maps?.places?.Autocomplete) {
          throw new Error("Google Maps Places library failed to load.");
        }
        autocomplete = new window.google.maps.places.Autocomplete(inputRef.current, {
          fields: ["place_id", "formatted_address", "geometry", "name"],
          types: ["geocode"],
        });
        listener = autocomplete.addListener("place_changed", () => {
          const place = autocomplete.getPlace();
          const location = place.geometry?.location;
          if (!place.place_id || !place.formatted_address || !location) {
            onPlaceCleared();
            return;
          }
          applyingSelectionRef.current = true;
          selectedTextsRef.current = new Set(
            [place.formatted_address, place.name, inputRef.current?.value].filter(Boolean),
          );
          onPlaceSelected({
            address: place.formatted_address,
            google_place_id: place.place_id,
            latitude: location.lat(),
            longitude: location.lng(),
          });
          window.setTimeout(() => {
            applyingSelectionRef.current = false;
          }, 0);
        });
      })
      .catch((error) => {
        if (!cancelled) setMapsError(error.message);
      });

    return () => {
      cancelled = true;
      if (listener) {
        window.google?.maps?.event?.removeListener(listener);
      }
      if (autocomplete) {
        window.google?.maps?.event?.clearInstanceListeners(autocomplete);
      }
    };
  }, [onPlaceCleared, onPlaceSelected]);

  function handleChange(event) {
    const text = event.target.value;
    onChange(text);
    if (applyingSelectionRef.current || selectedTextsRef.current.has(text)) {
      return;
    }
    selectedTextsRef.current = new Set();
    onPlaceCleared();
  }

  return (
    <label htmlFor={id}>
      Address
      <input
        id={id}
        ref={inputRef}
        name="address"
        value={value}
        onChange={handleChange}
        autoComplete="off"
        required
      />
      {mapsError ? <p className="error">{mapsError}</p> : null}
    </label>
  );
}

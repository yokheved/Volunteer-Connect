import { useEffect, useRef, useState } from "react";
import { loadGooglePlaces } from "../services/googlePlaces";

const FOCUS_BROWN = "#6b5344";
const REST_BORDER = "#c5c0b5";

function isBlue(color) {
  const match = String(color).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!match) return false;
  const red = Number(match[1]);
  const green = Number(match[2]);
  const blue = Number(match[3]);
  return blue > 120 && blue > red + 30 && blue > green + 20;
}

function paintFocusBrown(widget) {
  const root = widget.shadowRoot;
  if (!root) return;
  const nodes = [widget, ...root.querySelectorAll("*")];
  for (const node of nodes) {
    const style = getComputedStyle(node);
    const blueBorder = isBlue(style.borderTopColor);
    const blueOutline = isBlue(style.outlineColor);
    const blueShadow = isBlue(style.boxShadow);
    if (!blueBorder && !blueOutline && !blueShadow) continue;
    if (blueBorder) node.style.setProperty("border-color", FOCUS_BROWN, "important");
    if (blueOutline) node.style.setProperty("outline-color", FOCUS_BROWN, "important");
    if (blueShadow) node.style.setProperty("box-shadow", "none", "important");
  }
}

function installAddressStyles(widget) {
  const root = widget.shadowRoot;
  if (!root || root.querySelector("[data-address-focus]")) return;
  const style = document.createElement("style");
  style.dataset.addressFocus = "true";
  style.textContent = `
    :host {
      --gmp-mat-color-primary: ${FOCUS_BROWN} !important;
      --gmp-mat-color-outline: ${REST_BORDER} !important;
      --md-sys-color-primary: ${FOCUS_BROWN} !important;
    }
    :host(:focus-within) {
      border-color: ${FOCUS_BROWN} !important;
      outline-color: ${FOCUS_BROWN} !important;
    }
    input, textarea {
      border-color: ${REST_BORDER} !important;
      outline: none !important;
      box-shadow: none !important;
    }
    input:focus, input:focus-visible, textarea:focus {
      border-color: ${FOCUS_BROWN} !important;
      outline-color: ${FOCUS_BROWN} !important;
      box-shadow: none !important;
    }
  `;
  root.appendChild(style);
}

export default function AddressAutocomplete({
  id,
  value,
  onChange,
  onPlaceSelected,
  onPlaceCleared,
}) {
  const hostRef = useRef(null);
  const valueRef = useRef(value);
  const onChangeRef = useRef(onChange);
  const onPlaceSelectedRef = useRef(onPlaceSelected);
  const onPlaceClearedRef = useRef(onPlaceCleared);
  const applyingSelectionRef = useRef(false);
  const [mapsError, setMapsError] = useState("");

  valueRef.current = value;
  onChangeRef.current = onChange;
  onPlaceSelectedRef.current = onPlaceSelected;
  onPlaceClearedRef.current = onPlaceCleared;

  useEffect(() => {
    let cancelled = false;
    let widget;

    loadGooglePlaces()
      .then(() => {
        if (cancelled || !hostRef.current) {
          return;
        }
        const PlaceAutocompleteElement = window.google?.maps?.places?.PlaceAutocompleteElement;
        if (typeof PlaceAutocompleteElement !== "function") {
          throw new Error("Google Maps Places library failed to load.");
        }
        widget = new PlaceAutocompleteElement();
        widget.id = id;
        widget.value = valueRef.current || "";
        hostRef.current.replaceChildren(widget);
        installAddressStyles(widget);
        widget.addEventListener("focusin", () => {
          paintFocusBrown(widget);
          window.requestAnimationFrame(() => paintFocusBrown(widget));
        });

        widget.addEventListener("input", () => {
          if (applyingSelectionRef.current) {
            return;
          }
          onChangeRef.current(widget.value || "");
          onPlaceClearedRef.current();
        });

        widget.addEventListener("gmp-select", async (event) => {
          applyingSelectionRef.current = true;
          try {
            const placePrediction = event.placePrediction;
            const place = placePrediction.toPlace();
            await place.fetchFields({
              fields: ["id", "formattedAddress", "location"],
            });
            const location = place.location;
            const latitude =
              location && (typeof location.lat === "function" ? location.lat() : location.lat);
            const longitude =
              location && (typeof location.lng === "function" ? location.lng() : location.lng);
            const placeId = place.id || placePrediction.placeId || "";
            const address = place.formattedAddress || "";
            if (!placeId || !address || latitude == null || longitude == null) {
              onPlaceClearedRef.current();
              return;
            }
            onChangeRef.current(address);
            onPlaceSelectedRef.current({
              address,
              google_place_id: placeId,
              latitude,
              longitude,
            });
          } catch {
            onPlaceClearedRef.current();
          } finally {
            window.setTimeout(() => {
              applyingSelectionRef.current = false;
            }, 0);
          }
        });
      })
      .catch((error) => {
        if (!cancelled) setMapsError(error.message);
      });

    return () => {
      cancelled = true;
      widget?.remove();
    };
  }, [id]);

  return (
    <label htmlFor={id} className="address-field">
      Address
      <div ref={hostRef} />
      {mapsError ? <p className="error">{mapsError}</p> : null}
    </label>
  );
}

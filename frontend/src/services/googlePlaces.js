const SCRIPT_ID = "google-maps-places-script";
const CALLBACK_NAME = "__volunteerConnectMapsReady";

let loadPromise;

export function getGoogleMapsApiKey() {
  const key = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  if (!key || key === "example_api_key") {
    return "";
  }
  return key;
}

export function loadGooglePlaces() {
  const key = getGoogleMapsApiKey();
  if (!key) {
    return Promise.reject(
      new Error("Google Maps API key is missing. Set VITE_GOOGLE_MAPS_API_KEY."),
    );
  }
  if (loadPromise) {
    return loadPromise;
  }

  loadPromise = injectMapsScript(key)
    .then(() => {
      if (typeof window.google?.maps?.importLibrary !== "function") {
        throw new Error("Google Maps failed to load.");
      }
      return window.google.maps.importLibrary("places");
    })
    .then(() => {
      if (!window.google?.maps?.places) {
        throw new Error("Google Maps Places library failed to load.");
      }
    })
    .catch((error) => {
      loadPromise = null;
      if (error instanceof Error && error.message.startsWith("Google Maps")) {
        throw error;
      }
      throw new Error("Google Maps failed to load.");
    });

  return loadPromise;
}

function injectMapsScript(key) {
  if (typeof window.google?.maps?.importLibrary === "function") {
    return Promise.resolve();
  }

  return new Promise((resolve, reject) => {
    const fail = () => reject(new Error("Google Maps failed to load."));
    const existing = document.getElementById(SCRIPT_ID);
    if (existing) {
      if (typeof window.google?.maps?.importLibrary === "function") {
        resolve();
        return;
      }
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", fail, { once: true });
      return;
    }

    window[CALLBACK_NAME] = () => {
      delete window[CALLBACK_NAME];
      resolve();
    };

    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.async = true;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&loading=async&callback=${CALLBACK_NAME}`;
    script.onerror = () => {
      delete window[CALLBACK_NAME];
      fail();
    };
    document.head.appendChild(script);
  });
}

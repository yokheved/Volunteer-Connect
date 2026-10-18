export function splitDisplayName(name) {
  const trimmed = (name || "").trim();
  const index = trimmed.lastIndexOf(" ");
  if (index === -1) {
    return { firstName: trimmed, lastName: "" };
  }
  return {
    firstName: trimmed.slice(0, index).trim(),
    lastName: trimmed.slice(index + 1).trim(),
  };
}

export function joinDisplayName(firstName, lastName) {
  return [firstName, lastName]
    .map((part) => (part || "").trim())
    .filter(Boolean)
    .join(" ");
}

from marshmallow import Schema, fields, pre_load, validate


class LocationFieldsSchema(Schema):
    address = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    google_place_id = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))

    @pre_load
    def strip_location_text(self, data, **_kwargs):
        if not isinstance(data, dict):
            return data
        stripped = dict(data)
        for key in ("address", "google_place_id"):
            value = stripped.get(key)
            if isinstance(value, str):
                stripped[key] = value.strip()
        return stripped

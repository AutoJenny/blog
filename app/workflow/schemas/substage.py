from marshmallow import Schema, fields

class SubstageSchema(Schema):
    id = fields.Int(dump_only=True)
    stage_id = fields.Int(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    substage_order = fields.Int(required=True)
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True) 
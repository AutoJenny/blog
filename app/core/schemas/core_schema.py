from marshmallow import Schema, fields

class CoreSchema(Schema):
    id = fields.Int(required=True)
    name = fields.Str(required=True) 
from marshmallow import Schema, fields

class ActionSchema(Schema):
    id = fields.Int()
    field_name = fields.Str()
    prompt_template = fields.Str()
    prompt_template_id = fields.Int()
    llm_model = fields.Str()
    temperature = fields.Float()
    max_tokens = fields.Int()
    order = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    input_field = fields.Str()
    output_field = fields.Str()
    provider_id = fields.Int()
    timeout = fields.Int()

class ActionRunSchema(Schema):
    id = fields.Int()
    action_id = fields.Int()
    post_id = fields.Int()
    input_text = fields.Str()
    output_text = fields.Str()
    status = fields.Str()
    error_message = fields.Str()
    created_at = fields.DateTime() 
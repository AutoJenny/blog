def execute_action(action, input_data):
    # TODO: Replace with real logic
    class DummyRun:
        def __init__(self):
            self.id = 1
            self.action_id = 1
            self.post_id = 1
            self.input_text = str(input_data)
            self.output_text = "Dummy output"
            self.status = "completed"
            self.error_message = None
            from datetime import datetime
            self.created_at = datetime.utcnow()
    return DummyRun() 
from datetime import datetime


def inject_year():
    return {"current_year": datetime.now().year}

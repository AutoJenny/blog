from datetime import datetime


def inject_year():
    return {"year": datetime.now().year}

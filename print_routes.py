from app import create_app

app = create_app()

with app.app_context():
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.rule:40} {sorted([m for m in rule.methods if m not in ('HEAD', 'OPTIONS')])}") 
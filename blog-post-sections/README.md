# Blog Post Sections Microservice

This microservice powers the green Sections panel in the writing stage of BlogForge.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```

The service will be available at http://localhost:5003/

## Development
- Edit `templates/index.html` for the UI.
- Add Flask routes and logic in `app.py`.

## Integration
- This service is embedded in blog-core (port 5001) as an iframe in the writing stage. 
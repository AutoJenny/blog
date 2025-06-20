from flask import jsonify, current_app, request
from app.api import bp
import datetime
import psutil
import os
import requests
import time
import openai
from slugify import slugify
import subprocess
import glob
import shutil
import random as _random
import sys
from dotenv import dotenv_values
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from app.llm.services import LLMService
from app.database.routes import get_db_conn


def check_ollama_performance():
    """Check Ollama's performance for different operations."""
    ollama_url = current_app.config.get("OLLAMA_API_URL", "http://localhost:11434")
    performance = {
        "status": "healthy",
        "api_url": ollama_url,
        "operations": {},
        "benchmarks": {},
    }

    try:
        # Test model listing
        start_time = time.time()
        response = requests.get(f"{ollama_url}/api/tags")
        list_time = time.time() - start_time

        if response.status_code == 200:
            models = response.json().get("models", [])
            performance["available_models"] = [model["name"] for model in models]
            performance["operations"]["list_models"] = {
                "latency": round(list_time * 1000, 2),  # Convert to ms
                "status": "success",
            }

            # Select test models for benchmarking
            test_models = {
                "embedding": "nomic-embed-text:latest",  # Fast embedding model
                "completion": "mistral:latest",  # Fast completion model
            }

            # Test embedding performance
            start_time = time.time()
            embed_response = requests.post(
                f"{ollama_url}/api/embeddings",
                json={
                    "model": test_models["embedding"],
                    "prompt": "Test embedding performance",
                },
            )
            embed_time = time.time() - start_time

            if embed_response.status_code == 200:
                performance["benchmarks"]["embedding"] = {
                    "model": test_models["embedding"],
                    "latency": round(embed_time * 1000, 2),
                    "status": "success",
                }

            # Test completion performance with different lengths
            for length in ["short", "medium"]:
                prompt = (
                    "Hi"
                    if length == "short"
                    else "Write a brief paragraph about performance testing."
                )
                start_time = time.time()
                gen_response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": test_models["completion"],
                        "prompt": prompt,
                        "stream": False,
                        "raw": True,  # Get raw performance metrics
                    },
                )
                gen_time = time.time() - start_time

                if gen_response.status_code == 200:
                    performance["benchmarks"][f"{length}_completion"] = {
                        "model": test_models["completion"],
                        "prompt_length": len(prompt),
                        "latency": round(gen_time * 1000, 2),
                        "status": "success",
                    }

            # Test model load times (non-blocking)
            for model_type, model in test_models.items():
                start_time = time.time()
                load_response = requests.post(
                    f"{ollama_url}/api/show", json={"name": model}, timeout=2
                )
                load_time = time.time() - start_time

                if load_response.status_code == 200:
                    model_info = load_response.json()
                    performance["benchmarks"][f"{model_type}_model_info"] = {
                        "model": model,
                        "load_latency": round(load_time * 1000, 2),
                        "parameters": model_info.get("parameters"),
                        "format": model_info.get("format"),
                        "families": model_info.get("families", []),
                        "status": "success",
                    }

    except Exception as e:
        performance["status"] = "degraded"
        performance["error"] = str(e)

    return performance


def _get_client():
    """Get an authenticated client"""
    auth = current_app.config.get("OPENAI_AUTH_TOKEN")
    if not auth:
        raise ValueError("Authentication token not configured")
    return openai.OpenAI(default_headers={"Authorization": f"Bearer {auth}"})


@bp.route("/health/openai")
def check_openai():
    """Check OpenAI's performance and availability."""
    try:
        auth = current_app.config.get("OPENAI_AUTH_TOKEN")
        if not auth:
            raise ValueError("Authentication token not configured")

        # client = openai.OpenAI(auth=ServiceAuth(auth))
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=5,
        )
        latency = (time.time() - start_time) * 1000  # Convert to ms

        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "model": "gpt-3.5-turbo",
        }
    except Exception as e:
        current_app.logger.error(f"OpenAI health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e), "model": "gpt-3.5-turbo"}


def check_dependencies():
    """Check for outdated or deprecated dependencies."""
    try:
        import pkg_resources
        from packaging import version

        critical_packages = {
            "langchain": "0.3.23",
            "langchain-community": "0.3.21",
            "langchain-core": "0.3.55",
            "openai": "1.12.0",
        }

        dependency_status = {
            "status": "healthy",
            "outdated_packages": [],
            "deprecated_packages": [],
        }

        for package, min_version in critical_packages.items():
            try:
                installed = pkg_resources.get_distribution(package)
                if version.parse(installed.version) < version.parse(min_version):
                    dependency_status["outdated_packages"].append(
                        {
                            "package": package,
                            "installed": installed.version,
                            "required": min_version,
                        }
                    )
            except pkg_resources.DistributionNotFound:
                dependency_status["outdated_packages"].append(
                    {
                        "package": package,
                        "installed": "not found",
                        "required": min_version,
                    }
                )

        if dependency_status["outdated_packages"]:
            dependency_status["status"] = "degraded"

        return dependency_status
    except Exception as e:
        current_app.logger.error(f"Dependency check failed: {str(e)}")
        return {"status": "error", "error": str(e)}


@bp.route("/health")
def health_check():
    """Check the health of the application and its dependencies."""
    # Support both /api/health and /v1/health paths
    is_v1 = request.path.startswith("/v1/")

    # Basic response for v1 health check (for legacy support)
    if is_v1:
        return jsonify(
            {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
        )

    # Full health check
    health_status = {
        "status": "healthy",
        "database": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": current_app.config.get("ENV", "production"),
        "debug_mode": current_app.debug,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage("/")._asdict(),
        },
        "dependencies": check_dependencies(),
        "llm_services": {},
    }

    # Check Ollama (primary LLM)
    health_status["llm_services"]["ollama"] = check_ollama_performance()
    if health_status["llm_services"]["ollama"]["status"] == "degraded":
        health_status["status"] = "degraded"

    # Check OpenAI (secondary LLM)
    health_status["llm_services"]["openai"] = check_openai()
    if health_status["llm_services"]["openai"].get("status") == "unhealthy":
        health_status["status"] = "degraded"

    # Overall status determination
    if health_status["dependencies"]["status"] == "degraded":
        health_status["status"] = "degraded"

    response = jsonify(health_status)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@bp.route("/posts", methods=["GET"])
def list_posts():
    print("[DEBUG] Entered list_posts endpoint", flush=True)
    # Return all posts as JSON, including idea_seed and substage_id.
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.title, p.slug, p.summary, p.created_at, p.updated_at, p.header_image_id, p.status, pd.idea_seed, p.substage_id
                FROM post p
                LEFT JOIN post_development pd ON p.id = pd.post_id
                ORDER BY p.created_at DESC
            """)
            posts = cur.fetchall()
            # Convert datetime to isoformat and return as list of dicts
            result = []
            for post in posts:
                result.append({
                    "id": post["id"],
                    "title": post["title"],
                    "slug": post["slug"],
                    "summary": post["summary"],
                    "created_at": post["created_at"].isoformat() if post["created_at"] else None,
                    "updated_at": post["updated_at"].isoformat() if post["updated_at"] else None,
                    "header_image_id": post["header_image_id"],
                    "status": post["status"],
                    "idea_seed": post["idea_seed"],
                    "substage_id": post["substage_id"],
                })
            return jsonify(result), 200


@bp.route("/posts", methods=["POST"])
def create_post():
    data = request.get_json() or {}
    title = data.get("title", "Untitled")
    content = data.get("content", "")
    author_id = data.get("author_id")
    # Generate slug
    base_slug = slugify(title)
    counter = 0
    slug = base_slug
    while Post.query.filter_by(slug=slug).first():
        counter += 1
        slug = f"{base_slug}-{counter}"
    post = Post()
    post.title = title
    post.content = content
    post.slug = slug
    db.session.add(post)
    db.session.commit()
    return (
        jsonify(
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "slug": post.slug,
            }
        ),
        201,
    )


# --- ImageStyle CRUD API endpoints ---
@bp.route("/images/styles", methods=["GET"])
def list_image_styles():
    styles = ImageStyle.query.order_by(ImageStyle.title).all()
    return jsonify([s.to_dict() for s in styles]), 200

@bp.route("/images/styles/<int:style_id>", methods=["GET"])
def get_image_style(style_id):
    style = ImageStyle.query.get(style_id)
    if not style:
        return jsonify({"error": "Style not found"}), 404
    return jsonify(style.to_dict()), 200

@bp.route("/images/styles", methods=["POST"])
def create_image_style():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if ImageStyle.query.filter_by(title=title).first():
        return jsonify({"error": "Style with this title already exists"}), 400
    style = ImageStyle(title=title, description=description)
    db.session.add(style)
    db.session.commit()
    return jsonify(style.to_dict()), 201

@bp.route("/images/styles/<int:style_id>", methods=["PUT"])
def update_image_style(style_id):
    style = ImageStyle.query.get(style_id)
    if not style:
        return jsonify({"error": "Style not found"}), 404
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    if title:
        # Check for duplicate title
        existing = ImageStyle.query.filter_by(title=title).first()
        if existing and existing.id != style_id:
            return jsonify({"error": "Style with this title already exists"}), 400
        style.title = title
    if description is not None:
        style.description = description
    db.session.commit()
    return jsonify(style.to_dict()), 200

@bp.route("/images/styles/<int:style_id>", methods=["DELETE"])
def delete_image_style(style_id):
    style = ImageStyle.query.get(style_id)
    if not style:
        return jsonify({"error": "Style not found"}), 404
    db.session.delete(style)
    db.session.commit()
    return jsonify({"result": "deleted"}), 200


# --- ImageFormat CRUD API endpoints ---
@bp.route("/images/formats", methods=["GET"])
def list_image_formats():
    formats = ImageFormat.query.order_by(ImageFormat.title).all()
    return jsonify([f.to_dict() for f in formats]), 200

@bp.route("/images/formats/<int:format_id>", methods=["GET"])
def get_image_format(format_id):
    fmt = ImageFormat.query.get(format_id)
    if not fmt:
        return jsonify({"error": "Format not found"}), 404
    return jsonify(fmt.to_dict()), 200

@bp.route("/images/formats", methods=["POST"])
def create_image_format():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    width = data.get("width")
    height = data.get("height")
    steps = data.get("steps")
    guidance_scale = data.get("guidance_scale")
    extra_settings = data.get("extra_settings")
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if ImageFormat.query.filter_by(title=title).first():
        return jsonify({"error": "Format with this title already exists"}), 400
    fmt = ImageFormat(
        title=title,
        description=description,
        width=width,
        height=height,
        steps=steps,
        guidance_scale=guidance_scale,
        extra_settings=extra_settings
    )
    db.session.add(fmt)
    db.session.commit()
    return jsonify(fmt.to_dict()), 201

@bp.route("/images/formats/<int:format_id>", methods=["PUT"])
def update_image_format(format_id):
    fmt = ImageFormat.query.get(format_id)
    if not fmt:
        return jsonify({"error": "Format not found"}), 404
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    width = data.get("width")
    height = data.get("height")
    steps = data.get("steps")
    guidance_scale = data.get("guidance_scale")
    extra_settings = data.get("extra_settings")
    if title:
        existing = ImageFormat.query.filter_by(title=title).first()
        if existing and existing.id != format_id:
            return jsonify({"error": "Format with this title already exists"}), 400
        fmt.title = title
    if description is not None:
        fmt.description = description
    if width is not None:
        fmt.width = width
    if height is not None:
        fmt.height = height
    if steps is not None:
        fmt.steps = steps
    if guidance_scale is not None:
        fmt.guidance_scale = guidance_scale
    if extra_settings is not None:
        fmt.extra_settings = extra_settings
    db.session.commit()
    return jsonify(fmt.to_dict()), 200

@bp.route("/images/formats/<int:format_id>", methods=["DELETE"])
def delete_image_format(format_id):
    fmt = ImageFormat.query.get(format_id)
    if not fmt:
        return jsonify({"error": "Format not found"}), 404
    db.session.delete(fmt)
    db.session.commit()
    return jsonify({"result": "deleted"}), 200


# --- ImageSetting CRUD API ---
@bp.route('/images/settings', methods=['GET'])
def list_image_settings():
    settings = ImageSetting.query.order_by(ImageSetting.name).all()
    return jsonify([s.to_dict() for s in settings])

@bp.route('/images/settings/<int:setting_id>', methods=['GET'])
def get_image_setting(setting_id):
    s = ImageSetting.query.get(setting_id)
    if not s:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(s.to_dict())

@bp.route('/images/settings', methods=['POST'])
def create_image_setting():
    data = request.get_json() or {}
    name = data.get('name')
    style_id = data.get('style_id')
    format_id = data.get('format_id')
    width = data.get('width')
    height = data.get('height')
    steps = data.get('steps')
    guidance_scale = data.get('guidance_scale')
    extra_settings = data.get('extra_settings')
    if not name or not style_id or not format_id:
        return jsonify({'error': 'Missing required fields'}), 400
    if ImageSetting.query.filter_by(name=name).first():
        return jsonify({'error': 'Name already exists'}), 400
    style = ImageStyle.query.get(style_id)
    fmt = ImageFormat.query.get(format_id)
    if not style or not fmt:
        return jsonify({'error': 'Invalid style or format'}), 400
    s = ImageSetting(
        name=name,
        style_id=style_id,
        format_id=format_id,
        width=width,
        height=height,
        steps=steps,
        guidance_scale=guidance_scale,
        extra_settings=extra_settings
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201

@bp.route('/images/settings/<int:setting_id>', methods=['PUT'])
def update_image_setting(setting_id):
    s = ImageSetting.query.get(setting_id)
    if not s:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    name = data.get('name')
    style_id = data.get('style_id')
    format_id = data.get('format_id')
    width = data.get('width')
    height = data.get('height')
    steps = data.get('steps')
    guidance_scale = data.get('guidance_scale')
    extra_settings = data.get('extra_settings')
    if name:
        existing = ImageSetting.query.filter_by(name=name).first()
        if existing and existing.id != setting_id:
            return jsonify({'error': 'Name already exists'}), 400
        s.name = name
    if style_id:
        style = ImageStyle.query.get(style_id)
        if not style:
            return jsonify({'error': 'Invalid style'}), 400
        s.style_id = style_id
    if format_id:
        fmt = ImageFormat.query.get(format_id)
        if not fmt:
            return jsonify({'error': 'Invalid format'}), 400
        s.format_id = format_id
    if width is not None:
        s.width = width
    if height is not None:
        s.height = height
    if steps is not None:
        s.steps = steps
    if guidance_scale is not None:
        s.guidance_scale = guidance_scale
    if extra_settings is not None:
        s.extra_settings = extra_settings
    db.session.commit()
    return jsonify(s.to_dict())

@bp.route('/images/settings/<int:setting_id>', methods=['DELETE'])
def delete_image_setting(setting_id):
    s = ImageSetting.query.get(setting_id)
    if not s:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/comfyui/status', methods=['GET'])
def comfyui_status():
    """Check if ComfyUI is running (by process name and port)."""
    # Check for process
    running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'main.py' in proc.info['cmdline'] and 'ComfyUI' in ' '.join(proc.info['cmdline']):
                running = True
                break
        except Exception:
            continue
    return jsonify({"running": running})

@bp.route('/comfyui/start', methods=['POST'])
def comfyui_start():
    """Start ComfyUI if not running."""
    # Check if already running
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'main.py' in proc.info['cmdline'] and 'ComfyUI' in ' '.join(proc.info['cmdline']):
                return jsonify({"started": False, "running": True})
        except Exception:
            continue
    # Not running, so start it
    comfyui_dir = os.path.expanduser('~/ComfyUI')
    venv_python = os.path.join(comfyui_dir, 'venv', 'bin', 'python')
    main_py = os.path.join(comfyui_dir, 'main.py')
    cmd = [venv_python, main_py, '--listen', '0.0.0.0', '--port', '8188']
    # Start in background, detach from Flask
    with open(os.devnull, 'w') as devnull:
        subprocess.Popen(cmd, cwd=comfyui_dir, stdout=devnull, stderr=devnull, preexec_fn=os.setpgrp)
    # Give it a few seconds to start
    time.sleep(3)
    # Check again
    running = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'main.py' in proc.info['cmdline'] and 'ComfyUI' in ' '.join(proc.info['cmdline']):
                running = True
                break
        except Exception:
            continue
    return jsonify({"started": True, "running": running})

@bp.route('/images/generate', methods=['POST'])
def generate_image():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    provider = data.get('provider', 'sd')  # Default to SD
    image_setting_id = data.get('image_setting_id')
    width = data.get('width')
    height = data.get('height')
    steps = data.get('steps')
    guidance_scale = data.get('guidance_scale')
    extra_settings = data.get('extra_settings')
    # If image_setting_id is provided, load settings from DB
    if image_setting_id:
        setting = ImageSetting.query.get(image_setting_id)
        if setting:
            width = width or setting.width
            height = height or setting.height
            steps = steps or setting.steps
            guidance_scale = guidance_scale or setting.guidance_scale
            extra_settings = extra_settings or setting.extra_settings
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    if provider == 'sd':
        # Compose workflow for SD3.5
        import time as _time
        unique_prefix = f"webui_sd35_{int(_time.time())}"
        # Set good defaults for SD3.5 Large
        width = int(width) if width else 1024
        height = int(height) if height else 1024
        steps = int(steps) if steps else 30
        guidance_scale = float(guidance_scale) if guidance_scale else 6.0
        seed = _random.randint(1, 2**31-1)
        negative_prompt = "blurry, low quality, bad anatomy, text, watermark, signature"
        workflow = {
            "prompt": {
                "1": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {"ckpt_name": "sd3.5_large.safetensors"}
                },
                "2": {
                    "class_type": "CLIPLoader",
                    "inputs": {"clip_name": "clip_g.safetensors", "type": "sd3"}
                },
                "3": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": prompt,
                        "clip": ["2", 0]
                    }
                },
                "8": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": negative_prompt,
                        "clip": ["2", 0]
                    }
                },
                "4": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1}
                },
                "5": {
                    "class_type": "KSampler",
                    "inputs": {
                        "model": ["1", 0],
                        "positive": ["3", 0],
                        "negative": ["8", 0],
                        "latent_image": ["4", 0],
                        "steps": steps,
                        "cfg": guidance_scale,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "seed": seed,
                        "denoise": 1.0
                    }
                },
                "6": {
                    "class_type": "VAEDecode",
                    "inputs": {
                        "samples": ["5", 0],
                        "vae": ["1", 2]
                    }
                },
                "7": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "images": ["6", 0],
                        "filename_prefix": unique_prefix
                    }
                }
            }
        }
        # Optionally merge extra_settings (if JSON)
        import json
        if extra_settings:
            try:
                extra = json.loads(extra_settings) if isinstance(extra_settings, str) else extra_settings
                # Merge into workflow as needed (advanced users only)
                # For now, ignore unless you want to support custom nodes/params
            except Exception:
                pass
        try:
            res = requests.post('http://localhost:8188/prompt', json=workflow, timeout=60)
            debug_info = {'comfyui_status_code': res.status_code, 'comfyui_response': res.text}
            if res.status_code != 200:
                return jsonify({'error': f'ComfyUI error: {res.text}', 'debug': debug_info}), 500
            # Wait for image to appear (poll for up to 5 minutes)
            output_dir = os.path.expanduser('~/ComfyUI/output/')
            prefix = unique_prefix
            found = None
            stable_count = 0
            last_size = -1
            for _ in range(300):  # Wait up to 5 minutes (300 seconds)
                files = sorted(glob.glob(os.path.join(output_dir, f'{prefix}_*.png')), key=os.path.getmtime, reverse=True)
                files_checked = files
                if files:
                    candidate = files[0]
                    size = os.path.getsize(candidate)
                    if size > 0:
                        if size == last_size:
                            stable_count += 1
                        else:
                            stable_count = 0
                        last_size = size
                        # Require 3 consecutive checks (3 seconds) of stable size
                        if stable_count >= 3:
                            found = candidate
                            break
                time.sleep(1)
            if not found:
                # Add more debug info: list all files in output dir
                all_files = sorted(glob.glob(os.path.join(output_dir, '*.png')), key=os.path.getmtime, reverse=True)
                return jsonify({'error': 'No image generated', 'debug': debug_info, 'files_checked': files_checked, 'all_png_files': all_files, 'debug_prompt': prompt, 'debug_settings': {
                    'width': width, 'height': height, 'steps': steps, 'guidance_scale': guidance_scale, 'extra_settings': extra_settings
                }, 'debug_workflow': workflow}), 500
            # Copy to static/comfyui_output/
            static_dir = os.path.join(current_app.root_path, 'static', 'comfyui_output')
            os.makedirs(static_dir, exist_ok=True)
            fname = os.path.basename(found)
            dest = os.path.join(static_dir, fname)
            shutil.copy2(found, dest)
            image_url = f'/static/comfyui_output/{fname}'
            return jsonify({'image_url': image_url, 'provider': 'sd', 'debug': debug_info, 'debug_prompt': prompt, 'debug_settings': {
                'width': width, 'height': height, 'steps': steps, 'guidance_scale': guidance_scale, 'extra_settings': extra_settings
            }, 'debug_workflow': workflow})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif provider == 'openai':
        # OpenAI DALL·E (v2/v3) - requires OPENAI_API_KEY in config
        api_key = current_app.config.get('OPENAI_AUTH_TOKEN')
        if not api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        size = f"{width or 1024}x{height or 1024}"
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1
            )
            image_url = response.data[0].url if response.data and response.data[0].url else None
            return jsonify({'image_url': image_url, 'provider': 'openai', 'debug': {}})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': f'Unknown provider: {provider}'}), 400

# --- ImagePromptExample CRUD API endpoints ---
@bp.route('/images/prompt_examples', methods=['GET'])
def list_prompt_examples():
    examples = ImagePromptExample.query.order_by(ImagePromptExample.created_at.desc()).all()
    return jsonify([e.to_dict() for e in examples]), 200

@bp.route('/images/prompt_examples/<int:example_id>', methods=['GET'])
def get_prompt_example(example_id):
    e = ImagePromptExample.query.get(example_id)
    if not e:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(e.to_dict()), 200

@bp.route('/images/prompt_examples', methods=['POST'])
def create_prompt_example():
    data = request.get_json() or {}
    description = data.get('description')
    style_id = data.get('style_id')
    format_id = data.get('format_id')
    provider = data.get('provider')
    image_setting_id = data.get('image_setting_id')
    if not description or not style_id or not format_id or not provider:
        return jsonify({'error': 'Missing required fields'}), 400
    style = ImageStyle.query.get(style_id)
    fmt = ImageFormat.query.get(format_id)
    if not style or not fmt:
        return jsonify({'error': 'Invalid style or format'}), 400
    example = ImagePromptExample(
        description=description,
        style_id=style_id,
        format_id=format_id,
        provider=provider,
        image_setting_id=image_setting_id
    )
    db.session.add(example)
    db.session.commit()
    return jsonify(example.to_dict()), 201

@bp.route('/images/prompt_examples/<int:example_id>', methods=['PUT'])
def update_prompt_example(example_id):
    e = ImagePromptExample.query.get(example_id)
    if not e:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    if 'description' in data:
        e.description = data['description']
    if 'style_id' in data:
        style = ImageStyle.query.get(data['style_id'])
        if not style:
            return jsonify({'error': 'Invalid style'}), 400
        e.style_id = data['style_id']
    if 'format_id' in data:
        fmt = ImageFormat.query.get(data['format_id'])
        if not fmt:
            return jsonify({'error': 'Invalid format'}), 400
        e.format_id = data['format_id']
    if 'provider' in data:
        e.provider = data['provider']
    if 'image_setting_id' in data:
        e.image_setting_id = data['image_setting_id']
    db.session.commit()
    return jsonify(e.to_dict()), 200

@bp.route('/images/prompt_examples/<int:example_id>', methods=['DELETE'])
def delete_prompt_example(example_id):
    e = ImagePromptExample.query.get(example_id)
    if not e:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(e)
    db.session.commit()
    return jsonify({'success': True}), 200

@bp.route('/api/v1/posts/<int:post_id>/generate_images', methods=['POST'])
def generate_images_for_post(post_id):
    post = Post.query.get_or_404(post_id)
    sections = PostSection.query.filter_by(post_id=post_id).order_by(PostSection.section_order).all()
    results = []
    for section in sections:
        # Get linked prompt example
        prompt_example = None
        if section.image_prompt_example_id:
            prompt_example = ImagePromptExample.query.get(section.image_prompt_example_id)
        # Fallback: use section heading as description if no prompt example
        description = prompt_example.description if prompt_example else (section.section_heading or '')
        style_id = prompt_example.style_id if prompt_example else None
        format_id = prompt_example.format_id if prompt_example else None
        provider = prompt_example.provider if prompt_example else 'sd'
        image_setting_id = prompt_example.image_setting_id if prompt_example else None
        # Get image setting
        setting = ImageSetting.query.get(image_setting_id) if image_setting_id else None
        width = setting.width if setting else None
        height = setting.height if setting else None
        steps = setting.steps if setting else None
        guidance_scale = setting.guidance_scale if setting else None
        extra_settings = setting.extra_settings if setting else None
        # Compose prompt
        prompt = description
        if setting:
            prompt += f"\nStyle: {setting.style.title if setting.style else ''}"
            prompt += f"\nFormat: {setting.format.title if setting.format else ''}"
        # Call image generation endpoint
        try:
            import requests
            resp = requests.post(
                request.url_root.rstrip('/') + '/api/v1/images/generate',
                json={
                    'prompt': prompt,
                    'provider': provider,
                    'image_setting_id': image_setting_id,
                    'width': width,
                    'height': height,
                    'steps': steps,
                    'guidance_scale': guidance_scale,
                    'extra_settings': extra_settings
                },
                timeout=120
            )
            data = resp.json()
            if resp.status_code == 200 and data.get('image_url'):
                section.generated_image_url = data['image_url']
                section.image_generation_metadata = data
                db.session.commit()
                results.append({'section_id': section.id, 'image_url': data['image_url'], 'provider': provider, 'status': 'success'})
            else:
                results.append({'section_id': section.id, 'error': data.get('error', 'Unknown error'), 'provider': provider, 'status': 'error'})
        except Exception as e:
            results.append({'section_id': section.id, 'error': str(e), 'provider': provider, 'status': 'error'})
    return jsonify({'results': results})

@bp.route("/debug/routes", methods=["GET"])
def debug_list_routes():
    """Return all registered routes and their methods for debugging."""
    from flask import current_app
    output = []
    for rule in current_app.url_map.iter_rules():
        # Only show routes for this blueprint (api/v1)
        if rule.rule.startswith("/api/v1"):
            output.append({
                "endpoint": rule.endpoint,
                "rule": rule.rule,
                "methods": sorted([m for m in rule.methods if m not in ("HEAD", "OPTIONS")]),
            })
    return jsonify(sorted(output, key=lambda x: x["rule"])), 200

# --- PostDevelopment Fields API ---
@bp.route("/post_development/fields", methods=["GET"])
def get_post_development_fields():
    try:
        # Load DATABASE_URL from assistant_config.env
        config = dotenv_values(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
        db_url = config.get('DATABASE_URL')
        if not db_url or db_url.strip() == '':
            return jsonify({"error": "DATABASE_URL is not set or is empty!"}), 500
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'post_development' AND column_name NOT IN ('id', 'post_id')")
                columns = [row["column_name"] for row in cur.fetchall()]
        return jsonify({"fields": columns})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/post/<int:post_id>/development", methods=["GET"])
def get_post_development(post_id):
    try:
        # Load DATABASE_URL from assistant_config.env
        config = dotenv_values(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assistant_config.env'))
        db_url = config.get('DATABASE_URL')
        if not db_url or db_url.strip() == '':
            return jsonify({"error": "DATABASE_URL is not set or is empty!"}), 500
        with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM post_development WHERE post_id = %s", (post_id,))
                dev = cur.fetchone()
        if not dev:
            return jsonify({"error": "Not found"}), 404
        # Exclude id and post_id
        return jsonify({k: v for k, v in dev.items() if k not in ["id", "post_id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/structure/plan", methods=["POST"])
def plan_structure():
    """Plan the structure of a post using a two-stage process:
    1. Create section structure
    2. Allocate ideas and facts to sections
    """
    data = request.get_json()
    if not data or "title" not in data or "idea" not in data:
        return jsonify({"error": "title and idea are required"}), 400

    # --- Stage 1: Create Section Structure ---
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get the Section Structure Creator action
                cur.execute("""
                    SELECT * FROM llm_action WHERE field_name = 'Section Structure Creator' LIMIT 1
                """)
                structure_action = cur.fetchone()
                if not structure_action:
                    return jsonify({"error": "Section Structure Creator Action not found"}), 500
                structure_action = dict(structure_action)

                # Get the Content Allocator action
                cur.execute("""
                    SELECT * FROM llm_action WHERE field_name = 'Content Allocator' LIMIT 1
                """)
                allocator_action = cur.fetchone()
                if not allocator_action:
                    return jsonify({"error": "Content Allocator Action not found"}), 500
                allocator_action = dict(allocator_action)

        # Prepare fields for structure creation
        structure_fields = {
            'input_text': data['idea'],  # Required by LLMService
            'title': data['title'],
            'idea': data['idea'],
            'facts': data.get('facts', [])
        }

        # Create initial section structure
        llm_service = LLMService()
        structure_result = llm_service.execute_action(structure_action, structure_fields)
        
        # Extract the sections array from the result
        sections = structure_result.get('sections', [])
        if not sections:
            return jsonify({"error": "Failed to create section structure"}), 500

        # --- Stage 2: Allocate Content to Sections ---
        allocation_fields = {
            'input_text': json.dumps(sections),  # Required by LLMService - pass sections as input
            'sections': sections,
            'ideas': data.get('ideas', []),
            'facts': data.get('facts', []),
            'title': data['title'],
            'idea': data['idea']
        }

        # Allocate content to sections
        allocation_result = llm_service.execute_action(allocator_action, allocation_fields)
        
        # Return the final structure with allocated content
        return jsonify({"sections": allocation_result.get('sections', sections)})

    except Exception as e:
        return jsonify({"error": f"Error planning structure: {str(e)}"}), 500

@bp.route("/structure/save/<int:post_id>", methods=["POST"])
def save_structure(post_id):
    """Save the structure of a post."""
    data = request.get_json()
    if not data or "sections" not in data:
        return jsonify({"error": "sections are required"}), 400

    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Delete existing sections
                cur.execute("DELETE FROM post_section WHERE post_id = %s", (post_id,))
                
                # Insert new sections
                for i, section in enumerate(data["sections"]):
                    cur.execute(
                        """
                        INSERT INTO post_section (
                            post_id, section_order, section_heading, 
                            section_description, first_draft
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            post_id,
                            i,
                            section.get("heading", ""),
                            section.get("description", ""),
                            section.get("first_draft", "")
                        )
                    )
                
                # Update post's updated_at
                cur.execute("UPDATE post SET updated_at = NOW() WHERE id = %s", (post_id,))
                conn.commit()

        return jsonify({
            "message": "Structure saved successfully",
            "sections": data["sections"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/posts/<int:post_id>/structure", methods=["GET"])
def get_structure(post_id):
    """Get the structure of a post."""
    try:
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                # Get post
                cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
                post = cur.fetchone()
                if not post:
                    return jsonify({"error": "Post not found"}), 404

                # Get sections
                cur.execute(
                    "SELECT * FROM post_section WHERE post_id = %s ORDER BY section_order",
                    (post_id,)
                )
                sections = cur.fetchall()

                return jsonify({
                    "post": {
                        "id": post["id"],
                        "title": post["title"],
                        "slug": post["slug"],
                        "updated_at": post["updated_at"].isoformat()
                    },
                    "sections": [
                        {
                            "id": section["id"],
                            "heading": section["section_heading"],
                            "description": section["section_description"],
                            "first_draft": section["first_draft"],
                            "order": section["section_order"]
                        }
                        for section in sections
                    ]
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/structure/generate", methods=["POST"])
def generate_structure():
    """Generate a section structure for a post using Ollama directly."""
    data = request.get_json()
    if not data or "title" not in data or "idea" not in data:
        return jsonify({"error": "title and idea are required"}), 400

    try:
        # Prepare the prompt
        prompt = f"""You are an expert editorial planner for long-form articles. Your task is to design a clear, engaging, and logically structured set of sections for a new article.

Title: {data['title']}
Basic Idea: {data['idea']}
Interesting Facts:
{data.get('facts', '')}

Please create a JSON array of sections, where each section has:
1. A clear, engaging heading
2. A brief description of what that section will cover

Output format:
{{
    "sections": [
        {{
            "heading": "Section Title",
            "description": "Brief description of what this section will cover"
        }},
        ...
    ]
}}

Ensure the sections flow logically and cover all aspects of the topic."""

        # Call Ollama
        response = requests.post('http://localhost:11434/api/generate', 
                               json={
                                   "model": "mistral",
                                   "prompt": prompt,
                                   "stream": False
                               })
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to generate structure"}), 500

        # Parse the response
        result = response.json()
        try:
            # Extract the JSON from the response
            sections_json = result['response']
            # Find the JSON object in the response
            json_start = sections_json.find('{')
            json_end = sections_json.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                return jsonify({"error": "Invalid response format"}), 500
            
            sections = json.loads(sections_json[json_start:json_end])
            return jsonify(sections)
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse LLM response"}), 500

    except Exception as e:
        return jsonify({"error": f"Error generating structure: {str(e)}"}), 500

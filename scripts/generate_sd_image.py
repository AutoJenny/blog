import requests
import json

# Minimal workflow for ComfyUI API
workflow = {
    "prompt": {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "v1-5-pruned-emaonly-fp16.safetensors"}
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "A Scottish castle on a misty morning",
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 512, "batch_size": 1}
        },
        "4": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["2", 0],
                "latent_image": ["3", 0],
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "seed": 42,
                "denoise": 1.0
            }
        },
        "5": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["4", 0],
                "vae": ["1", 2]
            }
        },
        "6": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["5", 0],
                "filename_prefix": "test_sd3.5"
            }
        }
    }
}

url = "http://localhost:8188/prompt"
headers = {"Content-Type": "application/json"}

response = requests.post(url, headers=headers, data=json.dumps(workflow))
print("API response:", response.status_code)
print(response.text)

try:
    data = response.json()
    # Try to extract output image path(s)
    if "output" in data:
        print("Output:", data["output"])
    elif "images" in data:
        print("Images:", data["images"])
except Exception as e:
    print("Could not parse JSON response:", e) 
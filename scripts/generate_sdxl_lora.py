#!/usr/bin/env python3
# Quick SDXL + LoRA runner (pen&ink + muted watercolor preset)
# Edit ONLY the three paths in CONFIG below, then run:
#   python generate_sdxl_lora.py --subject "a druid under an ancient oak, ritual, mystical, spiritual, ancient"

import argparse, os, torch, datetime
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler

# ====== CONFIG (EDIT THESE 3) ======
SDXL_BASE = "/PATH/TO/sdxl_base_1.0"               # e.g. "stabilityai/stable-diffusion-xl-base-1.0" OR local folder
LORA_PATH = "/PATH/TO/Aether_Watercolor_Ink.safetensors"  # your downloaded LoRA file
OUTPUT_DIR = "/PATH/TO/outputs"                    # where to save PNGs
# ===================================

STYLE_SENTENCE = (
    "loose pen-and-ink linework with watercolor washes, subdued earthy ochres, muted greens, soft blue tones, "
    "semi-transparent pigments, edges fading into white paper, visible paper texture, gentle warm golden glow, "
    "spiritual and ancient tone"
)

NEGATIVE = (
    "photorealism, oversaturated colors, neon, glossy digital look, hard poster edges, pure black heavy outlines, "
    "edge-to-edge coverage, flat fills, high contrast, comic cel shading"
)

def pick_device_dtype():
    if torch.cuda.is_available():
        return "cuda", torch.float16
    if torch.backends.mps.is_available():
        # Apple Silicon
        return "mps", torch.float16
    return "cpu", torch.float32

def main():
    parser = argparse.ArgumentParser(description="SDXL + LoRA quick test")
    parser.add_argument("--subject", required=True, help="Your concept/scene (content sentence)")
    parser.add_argument("--width", type=int, default=1792)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg", type=float, default=5.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lora_scale", type=float, default=0.85, help="0.7–1.0; lower = softer style")
    parser.add_argument("--filename", default="", help="Optional output filename (without extension)")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    device, dtype = pick_device_dtype()

    pipe = StableDiffusionXLPipeline.from_pretrained(
        SDXL_BASE, torch_dtype=dtype, use_safetensors=True
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)

    # Load LoRA
    pipe.load_lora_weights(LORA_PATH)
    # (Optional) fuse to speed up after testing; comment out if you want to change lora_scale between calls:
    # pipe.fuse_lora()

    generator = torch.Generator(device=device)
    generator = generator.manual_seed(args.seed)

    prompt = f"{args.subject}, mystical, spiritual, ancient"
    full_prompt = f"{prompt}, {STYLE_SENTENCE}"

    images = pipe(
        prompt=full_prompt,
        negative_prompt=NEGATIVE,
        num_inference_steps=args.steps,
        guidance_scale=args.cfg,
        width=args.width,
        height=args.height,
        generator=generator,
        cross_attention_kwargs={"scale": args.lora_scale},
    ).images

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = args.filename if args.filename else f"sdxl_inkwater_{ts}"
    out_path = os.path.join(OUTPUT_DIR, f"{base}_w{args.width}x{args.height}_cfg{args.cfg}_s{args.seed}.png")
    images[0].save(out_path)
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
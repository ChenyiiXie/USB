import os
import cv2
import numpy as np
import random
import argparse
import shutil
from pathlib import Path

class DrivingDataAugmentor:

    
    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    # Weather corruptions
    def add_brightness(self, image):
        """brightness increase"""
        factor = random.uniform(1.5, 3.0)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def add_dark(self, image):
        """dark environment"""
        factor = random.uniform(0.1, 0.4)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * factor, 0, 255)
        dark = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        noise = np.random.poisson(lam=15, size=dark.shape).astype(np.uint8)
        return cv2.add(dark, noise)

    def add_snow(self, image):
        """snowy weather"""
        h, w, _ = image.shape
        snow_num = random.randint(1500, 3500)
        whiten_intensity = random.uniform(0.15, 0.35)
        blur_len = random.randint(15, 30)
        
        # background whitening
        snow_bg = cv2.addWeighted(image, 1 - whiten_intensity,
                                  np.full_like(image, 255), whiten_intensity, 0)
        
        # generate snowflakes
        snow_layer = np.zeros((h, w), dtype=np.uint8)
        for _ in range(snow_num):
            x, y = random.randint(0, w - 1), random.randint(0, h - 1)
            r = random.randint(2, 8)
            cv2.circle(snow_layer, (x, y), r, 255, -1)
        
        # motion blur
        kernel = np.zeros((blur_len, blur_len))
        kernel[:, blur_len // 2] = 1
        kernel /= blur_len
        motion_blur = cv2.filter2D(snow_layer, -1, kernel)
        snow_rgb = cv2.cvtColor(motion_blur, cv2.COLOR_GRAY2BGR)
        
        return cv2.addWeighted(snow_bg, 1.0, snow_rgb, 0.7, 0)

    def add_fog(self, image):
        """foggy environment"""
        h, w, _ = image.shape
        fog_intensity = random.uniform(0.4, 0.8)
        
        # multi-scale fog layer
        fog_mask = np.zeros((h, w), np.float32)
        for scale in [0.02, 0.05, 0.1]:
            noise = np.random.rand(int(h * scale), int(w * scale))
            noise = cv2.resize(noise, (w, h))
            noise = cv2.GaussianBlur(noise, (0, 0), sigmaX=60)
            fog_mask += noise
        
        fog_mask = cv2.normalize(fog_mask, None, 0, 1, cv2.NORM_MINMAX)
        fog_layer = np.full_like(image, 255, dtype=np.float32)
        foggy = image.astype(np.float32) * (1 - fog_intensity * fog_mask[..., None]) \
              + fog_layer * (fog_intensity * fog_mask[..., None])
        
        return foggy.astype(np.uint8)

    def add_rain(self, image):
        """rainy environment"""
        h, w, _ = image.shape
        drop_num = random.randint(1500, 3000)
        blur_len = random.randint(20, 50)
        angle = random.uniform(-25, 25)
        
        # generate raindrops
        rain_layer = np.zeros((h, w), dtype=np.uint8)
        for _ in range(drop_num):
            x, y = random.randint(0, w - 1), random.randint(0, h - 1)
            cv2.circle(rain_layer, (x, y), 1, 255, -1)
        
        # motion blur
        kernel = np.zeros((blur_len, blur_len))
        kernel[:, blur_len // 2] = 1
        kernel /= blur_len
        M = cv2.getRotationMatrix2D((blur_len // 2, blur_len // 2), angle, 1.0)
        kernel = cv2.warpAffine(kernel, M, (blur_len, blur_len))
        motion_blur = cv2.filter2D(rain_layer, -1, kernel)
        rain_rgb = cv2.cvtColor(motion_blur, cv2.COLOR_GRAY2BGR)
        
        return cv2.addWeighted(image, 0.7, rain_rgb, 0.6, 0)

    # external occlusion
    def add_water_splash(self, image):
        """water splash occlusion"""
        h, w, _ = image.shape
        splash = image.copy()
        for _ in range(random.randint(40, 80)):
            x, y = random.randint(0, w-1), random.randint(0, h-1)
            r = random.randint(15, 70)
            overlay = splash.copy()
            cv2.circle(overlay, (x, y), r, (255, 255, 255), -1)
            splash = cv2.addWeighted(overlay, 0.3, splash, 0.7, 0)
        return cv2.GaussianBlur(splash, (21, 21), 10)

    def add_lens_obstacle(self, image):
        """lens occlusion"""
        h, w, _ = image.shape
        mask = np.ones((h, w), dtype=np.float32)
        for _ in range(random.randint(2, 6)):
            cx, cy = random.randint(0, w), random.randint(0, h)
            axes = (random.randint(80, 300), random.randint(80, 300))
            angle = random.randint(0, 180)
            cv2.ellipse(mask, (cx, cy), axes, angle, 0, 360, 0, -1)
        
        blurred = cv2.GaussianBlur(image, (51, 51), 50)
        mask = cv2.GaussianBlur(mask, (31, 31), 20)[..., None]
        return (image * mask + blurred * (1 - mask)).astype(np.uint8)

    # sensor failure
    def add_camera_crash(self, image):
        """camera crash"""
        return np.zeros_like(image)

    def add_frame_lost(self, image):
        """frame loss"""
        if random.random() < 0.5:
            return np.zeros_like(image)
        return image

    def add_saturate(self, image):
        """saturation shift"""
        factor = random.uniform(2.0, 4.0)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # motion blur
    def add_motion_blur(self, image):
        """motion blur"""
        ksize = random.randint(15, 35)
        kernel = np.zeros((ksize, ksize))
        kernel[ksize//2, :] = 1
        kernel /= ksize
        return cv2.filter2D(image, -1, kernel)

    def add_zoom_blur(self, image):
        """zoom blur"""
        h, w, _ = image.shape
        accum = np.zeros_like(image, dtype=np.float32)
        for i in range(1, 8):
            zoom = cv2.resize(image, None, fx=1+i*0.1, fy=1+i*0.1)
            zh, zw, _ = zoom.shape
            x1, y1 = (zw-w)//2, (zh-h)//2
            if x1 >= 0 and y1 >= 0:
                accum += zoom[y1:y1+h, x1:x1+w].astype(np.float32)
        return (accum/7).astype(np.uint8)

    # data transmission errors
    def add_bit_error(self, image):
        """bit error with random modes"""
        noisy = image.copy()
        h, w, c = noisy.shape
        
        # randomly choose an error mode
        error_mode = random.randint(1, 4)
        
        if error_mode == 1:
            # mode1：random pixel noise
            error_rate = random.uniform(0.01, 0.1)  # 1%-10%pixels
            mask = np.random.rand(h, w, c) < error_rate
            noisy[mask] = np.random.randint(0, 256, noisy[mask].shape, dtype=np.uint8)
        
        elif error_mode == 2:
            # mode2：random block error
            num_blocks = random.randint(5, 20)
            for _ in range(num_blocks):
                # random block size
                block_h = random.randint(10, 60)
                block_w = random.randint(10, 60)
                y = random.randint(0, max(0, h - block_h))
                x = random.randint(0, max(0, w - block_w))
                
                # block is either full noise or partial noise
                if random.random() < 0.5:
                    # full noise
                    noisy[y:y+block_h, x:x+block_w] = np.random.randint(
                        0, 256, (block_h, block_w, c), dtype=np.uint8
                    )
                else:
                    # partial noise
                    block_mask = np.random.rand(block_h, block_w) < 0.5
                    noisy[y:y+block_h, x:x+block_w][block_mask] = np.random.randint(
                        0, 256, (np.sum(block_mask), c), dtype=np.uint8
                    )
        
        elif error_mode == 3:
            # mode3：scanline error
            num_lines = random.randint(10, 40)
            for _ in range(num_lines):
                if random.random() < 0.5:
                    # horizontal line
                    y = random.randint(0, h-1)
                    noisy[y] = np.random.randint(0, 256, (w, c), dtype=np.uint8)
                else:
                    # vertical line
                    x = random.randint(0, w-1)
                    noisy[:, x] = np.random.randint(0, 256, (h, c), dtype=np.uint8)
        
        else:  # error_mode == 4
            # mode4：mixed severe error
            # some random pixels
            pixel_mask = np.random.rand(h, w, c) < 0.05
            noisy[pixel_mask] = np.random.randint(0, 256, np.sum(pixel_mask), dtype=np.uint8)
            
            # several error blocks
            for _ in range(random.randint(3, 10)):
                block_h = random.randint(20, 80)
                block_w = random.randint(20, 80)
                y = random.randint(0, max(0, h - block_h))
                x = random.randint(0, max(0, w - block_w))
                noisy[y:y+block_h, x:x+block_w] = np.random.randint(
                    0, 256, (block_h, block_w, c), dtype=np.uint8
                )
            
            # several scanlines
            for _ in range(random.randint(5, 15)):
                y = random.randint(0, h-1)
                noisy[y] = np.random.randint(0, 256, (w, c), dtype=np.uint8)
        
        return noisy

    def add_color_quant(self, image):
        """color quantization"""
        levels = random.randint(4, 16)
        div = 256 // levels
        return (image // div) * div

    def add_compression(self, image):
        """H.265compression artifacts"""
        quality = random.randint(3, 15)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, enc = cv2.imencode('.jpg', image, encode_param)
        return cv2.imdecode(enc, 1)
    
    # illumination corruptions
    def add_strong_glare(self, image):
        """strong glare from sunlight or headlights"""
        h, w, _ = image.shape
        # random glare position
        center = (random.randint(w//4, 3*w//4), random.randint(h//4, 3*h//4))
        radius = random.randint(150, 300)
        intensity = random.uniform(1.0, 1.5)
        
        mask = np.zeros((h, w), dtype=np.float32)
        cv2.circle(mask, center, radius, 1, -1)
        mask = cv2.GaussianBlur(mask, (0, 0), radius / 2)
        
        glare = image.astype(np.float32)
        for c in range(3):
            glare[:, :, c] = np.clip(glare[:, :, c] + intensity * 255 * mask, 0, 255)
        return glare.astype(np.uint8)

    def add_backlight(self, image):
        """backlight from sunrise or sunset"""
        h, w, _ = image.shape
        # create gradient mask
        y, x = np.ogrid[:h, :w]
        center_y = random.randint(0, h//3)  # sun position
        center_x = random.randint(w//4, 3*w//4)
        
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        mask = np.exp(-distance / (w * 0.3))
        
        backlit = image.astype(np.float32)
        backlit += mask[..., None] * 100  # increase brightness
        return np.clip(backlit, 0, 255).astype(np.uint8)
    
    # environmental pollution corruptions
    def add_sandstorm(self, image):
        """sandstorm with yellow tint and particle noise"""
        intensity = random.uniform(0.5, 0.8)
        # apply yellow tint
        sand_color = (140, 180, 200)  # BGRsand color in BGR format
        overlay = np.full(image.shape, sand_color, dtype=np.uint8)
        sandstorm = cv2.addWeighted(image, 1 - intensity, overlay, intensity, 0)
        
        # add sand particle noise
        noise = np.random.randint(0, 100, image.shape, dtype=np.uint8)
        sandstorm = cv2.add(sandstorm, noise // 5)
        
        # global blur
        return cv2.GaussianBlur(sandstorm, (11, 11), 15)

    def add_smoke(self, image):
        """smoke from fire or industrial pollution"""
        h, w, _ = image.shape
        smoke_intensity = random.uniform(0.5, 0.85)  # increase intensity range
        
        # generate layered irregular smoke masks
        smoke_mask = np.zeros((h, w), np.float32)
        
        # use smoke blobs at multiple sizes
        num_smoke_sources = random.randint(3, 8)
        for _ in range(num_smoke_sources):
            # random smoke source position
            center_x = random.randint(w//4, 3*w//4)
            center_y = random.randint(h//4, 3*h//4)
            
            # create one smoke blob
            size = random.randint(150, 400)
            y, x = np.ogrid[:h, :w]
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            smoke_cloud = np.exp(-distance / (size * 0.5))
            
            # add noise to make smoke more natural
            noise = np.random.rand(h, w) * 0.3
            smoke_cloud = smoke_cloud * (1 + noise)
            
            smoke_mask += smoke_cloud
        
        # normalize smoke mask
        smoke_mask = cv2.normalize(smoke_mask, None, 0, 1, cv2.NORM_MINMAX)
        
        # apply Gaussian blur to soften smoke
        smoke_mask = cv2.GaussianBlur(smoke_mask, (61, 61), 40)
        
        # smoke color with a visible gray tone
        smoke_color = np.full_like(image, (180, 180, 180), dtype=np.float32)  # brighter gray
        
        # add non-uniform smoke color variation
        color_variation = np.random.normal(0, 20, (h, w, 3))
        smoke_color = np.clip(smoke_color + color_variation, 0, 255)
        
        # blend original image and smoke
        smoky = image.astype(np.float32) * (1 - smoke_intensity * smoke_mask[..., None]) \
            + smoke_color * (smoke_intensity * smoke_mask[..., None])
        
        # reduce contrast because smoke lowers visibility
        smoky = smoky * 0.85 + 30  # slightly brighten and reduce contrast
        
        # add slight blur from smoke scattering
        smoky = cv2.GaussianBlur(smoky.astype(np.uint8), (5, 5), 2)
        
        return np.clip(smoky, 0, 255).astype(np.uint8)




    # extreme weather
    def add_lightning_flash(self, image):
        """lightning flash overexposure"""
        intensity = random.uniform(0.7, 1.5)
        flash_img = cv2.convertScaleAbs(image, alpha=intensity, beta=100)
        
        # random lightning path
        h, w, _ = image.shape
        mask = np.zeros((h, w), dtype=np.uint8)
        
        start_x, start_y = random.randint(0, w), 0
        for i in range(h // 10):
            end_x = start_x + random.randint(-50, 50)
            end_y = start_y + random.randint(20, 50)
            end_x = np.clip(end_x, 0, w - 1)
            end_y = np.clip(end_y, 0, h - 1)
            cv2.line(mask, (start_x, start_y), (end_x, end_y), 255, random.randint(10, 30))
            start_x, start_y = end_x, end_y
        
        mask = cv2.GaussianBlur(mask, (51, 51), 20) / 255.0
        mask = mask[..., None]
        
        return (flash_img * mask + image * (1 - mask)).astype(np.uint8)


    def get_all_corruptions(self):
        """get all corruption functions"""
        return {
            # 15 corruption types from the paper
            # Weather (5types)
            "bright": self.add_brightness,
            "dark": self.add_dark,
            "snow": self.add_snow,
            "fog": self.add_fog,
            "rain": self.add_rain,
            
            # external occlusion (2types)
            "splash": self.add_water_splash,
            "lens": self.add_lens_obstacle,
            
            # sensor failure (3types)
            "crash": self.add_camera_crash,
            "frame_lost": self.add_frame_lost,
            "saturate": self.add_saturate,
            
            # motion blur (2types)
            "motion_blur": self.add_motion_blur,
            "zoom_blur": self.add_zoom_blur,
            
            # data transmission errors (3types)
            "bit_error": self.add_bit_error,
            "quant": self.add_color_quant,
            "compress": self.add_compression,
            
            # additional corruption types
            # Illumination (2types)
            "glare": self.add_strong_glare,
            "backlight": self.add_backlight,
            
            # Environmental pollution (2types)
            "sandstorm": self.add_sandstorm,
            "smoke": self.add_smoke,
            
            # extreme weather (1types)
            "lightning": self.add_lightning_flash
            
        }

    def get_core_corruptions(self):
        """Get the core 15 corruptions from the paper"""
        core_corruptions = self.get_all_corruptions()
        # Keep only the core 15 corruptions
        core_keys = [
            "bright", "dark", "snow", "fog", "rain",
            "splash", "lens", "crash", "frame_lost", "saturate",
            "motion_blur", "zoom_blur", "bit_error", "quant", "compress"
        ]
        return {k: v for k, v in core_corruptions.items() if k in core_keys}

    def process_single_image(self, image_path, output_dir, use_extended=True):
        """
        Process one image and generate all corruptions
        
        Args:
            image_path: input image path
            output_dir: output root directory
            use_extended: whether to use extended corruptions, default true
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Unable to read image: {image_path}")
            return False
        
        # output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        image_name = Path(image_path).stem
        image_ext = Path(image_path).suffix
        
        print(f"Processing image: {image_path}")
        print(f"output directory: {output_dir}")
        
        # Select corruption functions
        if use_extended:
            corruptions = self.get_all_corruptions()
            print(f"Using extended mode: {len(corruptions)} corruptions")
        else:
            corruptions = self.get_core_corruptions()
            print(f"Using core mode: {len(corruptions)} corruptions")
        
        # Process each corruptions
        success_count = 0
        for corruption_name, corruption_func in corruptions.items():
            try:
                # Create corruption directory
                corruption_dir = output_path / corruption_name
                corruption_dir.mkdir(exist_ok=True)
                
                # Apply corruption
                corrupted_image = corruption_func(image.copy())
                
                # Save image
                output_filename = f"{image_name}_{corruption_name}{image_ext}"
                output_filepath = corruption_dir / output_filename
                cv2.imwrite(str(output_filepath), corrupted_image)
                
                print(f"  ✓ {corruption_name}")
                success_count += 1
                
            except Exception as e:
                print(f"  ✗ {corruption_name}: {e}")
        
        print(f"Done! successgenerated {success_count}/{len(corruptions)} corruptions")
        return True

    def process_folder(self, input_dir, output_dir, use_extended=True, skip_existing=True):
        """
        Batch process all images in a folder
        
        Args:
            input_dir: input folder path
            output_dir: output root directory
            use_extended: whether to use extended corruptions, default true
        """
        # Find image files
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"Input folder not found: {input_dir}")
            return False
        
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            image_files.extend(input_path.rglob(f"*{ext}"))
            image_files.extend(input_path.rglob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"No image files found: {input_dir}")
            return False
        
        # Select corruption functions
        if use_extended:
            corruptions = self.get_all_corruptions()
            print(f"Using extended mode: {len(corruptions)} corruptions")
        else:
            corruptions = self.get_core_corruptions()
            print(f"Using core mode: {len(corruptions)} corruptions")
        
        print(f"Found {len(image_files)} image files")
        print(f"Start batch processing...")
        
        # output directorystructure
        output_path = Path(output_dir)
        for corruption_name in corruptions.keys():
            (output_path / corruption_name).mkdir(parents=True, exist_ok=True)
        
        # Process each image files
        total_success = 0
        total_skip = 0
        for i, image_file in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] {image_file.name}")
            
            # Read image
            image = cv2.imread(str(image_file))
            if image is None:
                print(f"  Skip: unable to read")
                continue
            
            # Preserve folder structure
            rel_path = image_file.relative_to(input_path)
            image_name = image_file.stem
            image_ext = image_file.suffix
            
            # Process each corruptions
            file_success = 0
            file_skip = 0
            for corruption_name, corruption_func in corruptions.items():
                try:
                    # Create output path
                    corruption_output_dir = output_path / corruption_name / rel_path.parent
                    corruption_output_dir.mkdir(parents=True, exist_ok=True)
                    
                     # Check whether output exists
                    output_filename = f"{image_name}_{corruption_name}{image_ext}"
                    output_filepath = corruption_output_dir / output_filename
                    
                    if skip_existing and output_filepath.exists():
                        file_skip += 1
                        total_skip += 1
                        continue
                    
                    # Apply corruption
                    corrupted_image = corruption_func(image.copy())
                    
                    # Save image
                    #output_filename = f"{image_name}_{corruption_name}{image_ext}"
                    #output_filepath = corruption_output_dir / output_filename
                    cv2.imwrite(str(output_filepath), corrupted_image)
                    
                    file_success += 1
                    total_success += 1
                    
                except Exception as e:
                    print(f"  ✗ {corruption_name}: {e}")
            
            print(f"  Done: {file_success}/{len(corruptions)} corruptions")
        
        print(f"\nBatch processing done. Results saved to: {output_dir}")
        print(f"Total generated: {total_success} corrupted images")
        return True

    def process_first_moment_dataset(self, input_clean_dir, output_dir, use_extended=True, skip_existing=True, include_clean=True):
        """
        Generate a full variant dataset from first-timestamp clean data.

        Input layout:
            input_clean_dir/clean/<shard>/*

        Output layout:
            output_dir/clean/<shard>/*
            output_dir/<corruption>/<shard>/*_<corruption>.png + QA metadata
        """
        input_root = Path(input_clean_dir)
        clean_root = input_root / "clean" if (input_root / "clean").is_dir() else input_root
        if not clean_root.is_dir():
            print(f"cleanInput directory not found: {clean_root}")
            return False

        output_root = Path(output_dir)
        corruptions = self.get_all_corruptions() if use_extended else self.get_core_corruptions()
        shard_dirs = sorted([path for path in clean_root.iterdir() if path.is_dir() and "shard" in path.name])
        if not shard_dirs:
            print(f"No shard directories found: {clean_root}")
            return False

        if include_clean:
            print("Copy first-timestamp clean data")
            for shard_dir in shard_dirs:
                dst_shard = output_root / "clean" / shard_dir.name
                dst_shard.mkdir(parents=True, exist_ok=True)
                for src_file in shard_dir.iterdir():
                    if src_file.is_file():
                        dst_file = dst_shard / src_file.name
                        if not (skip_existing and dst_file.exists()):
                            shutil.copy2(src_file, dst_file)

        total_images = 0
        total_metadata = 0
        print(f"Generate{len(corruptions)}corruptions: {', '.join(corruptions.keys())}")

        for shard_dir in shard_dirs:
            image_files = sorted([
                path for path in shard_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp'}
            ])
            metadata_files = sorted([
                path for path in shard_dir.iterdir()
                if path.is_file() and path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.bmp'}
            ])
            print(f"Processing {shard_dir.name}: {len(image_files)} images, {len(metadata_files)} metadata files")

            for corruption_name, corruption_func in corruptions.items():
                dst_shard = output_root / corruption_name / shard_dir.name
                dst_shard.mkdir(parents=True, exist_ok=True)

                for metadata_file in metadata_files:
                    dst_file = dst_shard / metadata_file.name
                    if skip_existing and dst_file.exists():
                        continue
                    shutil.copy2(metadata_file, dst_file)
                    total_metadata += 1

                for image_file in image_files:
                    dst_name = f"{image_file.stem}_{corruption_name}{image_file.suffix}"
                    dst_file = dst_shard / dst_name
                    if skip_existing and dst_file.exists():
                        continue

                    image = cv2.imread(str(image_file))
                    if image is None:
                        print(f"  SkipUnable to read image: {image_file}")
                        continue

                    try:
                        corrupted_image = corruption_func(image.copy())
                        cv2.imwrite(str(dst_file), corrupted_image)
                        total_images += 1
                    except Exception as exc:
                        print(f"  {corruption_name}failed: {image_file.name}: {exc}")

        print(f"Variant data generation done: {total_images} images, {total_metadata} metadata copies")
        print(f"output directory: {output_root}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Generate corrupted variants from first-moment clean images.")
    parser.add_argument("--input_dir", default="./nuscenes_first_moment_clean",
                        help="Input clean first-moment directory. Accepts either <dir>/clean/<shard> or <dir>/<shard>.")
    parser.add_argument("--output_dir", default="./nuscenes_dataset_first",
                        help="Output variant dataset directory.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--core_only", action="store_true",
                        help="Generate only the core 15 corruptions instead of all corruptions.")
    parser.add_argument("--no_clean_copy", action="store_true",
                        help="Do not copy clean files into output_dir/clean.")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing output files.")
    args = parser.parse_args()

    augmentor = DrivingDataAugmentor(seed=args.seed)
    ok = augmentor.process_first_moment_dataset(
        args.input_dir,
        args.output_dir,
        use_extended=not args.core_only,
        skip_existing=not args.overwrite,
        include_clean=not args.no_clean_copy,
    )
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()

import cv2
import numpy as np
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

def load_depth_map(img_path):
    """
    Attempts to find and load a matching depth map for an RGB image.
    Naming: replaces 'rgb' with 'depth'.
    Formats: .npy or .png (16-bit).
    """
    # 1. Generate candidate paths
    name = img_path.name
    depth_name = name.replace("rgb", "depth")
    if depth_name == name:
        # Fallback if 'rgb' isn't in name
        depth_name = "depth_" + name
    
    # Explicitly avoid _vis files
    if "_vis" in name:
        return None
        
    candidates = [
        img_path.parent / (Path(depth_name).stem + ".npy"),
        img_path.parent / (Path(depth_name).stem + ".png"),
        # Sometimes depth might be in a different extension
        img_path.parent / depth_name
    ]
    
    for p in candidates:
        if p.exists() and "_vis" not in p.name:
            if p.suffix == '.npy':
                return np.load(p)
            else:
                # Assume 16-bit PNG
                depth = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
                if depth is not None:
                    return depth.astype(np.float32)
    return None

def calculate_depth_score(box_points, depth_map):
    """
    Scores a rectangle based on depth data:
    1. Planarity (Standard deviation of depth inside)
    2. Elevation (Contrast with surrounding background)
    """
    if depth_map is None:
        return 0.0
        
    mask = np.zeros(depth_map.shape, dtype=np.uint8)
    cv2.drawContours(mask, [box_points.astype(np.int32)], -1, 255, -1)
    
    depth_vals = depth_map[mask == 255]
    if len(depth_vals) < 10:
        return 0.0
        
    # 1. Planarity (0.0 to 1.0)
    # PCBs are flat. High std dev means it's likely a slanted surface or noise.
    std_dev = np.std(depth_vals)
    # Norm: Assume 10mm variance is 'bad'. This scale depends on depth units!
    # For now, we'll use a relative heuristic.
    planarity_score = np.exp(-std_dev / 50.0) 
    
    # 2. Elevation (0.0 to 1.0)
    # Dilation to get a surrounding 'ring'
    kernel = np.ones((7,7), np.uint8)
    dilated_mask = cv2.dilate(mask, kernel, iterations=2)
    ring_mask = cv2.bitwise_and(dilated_mask, cv2.bitwise_not(mask))
    
    outside_vals = depth_map[ring_mask == 255]
    if len(outside_vals) > 0:
        avg_inside = np.mean(depth_vals)
        avg_outside = np.mean(outside_vals)
        # Higher diff (if object is closer/higher) is better
        height_diff = abs(avg_inside - avg_outside)
        elevation_score = np.clip(height_diff / 100.0, 0, 1)
    else:
        elevation_score = 0.5
        
    return (planarity_score * 0.5) + (elevation_score * 0.5)

def detect_rectangles(image_path, depth_map=None, min_area_ratio=0.005, max_area_ratio=0.9):
    """
    Detects rectangles in an image and returns them with confidence scores.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"Error: Could not read image {image_path}")
        return []

    height, width = img.shape[:2]
    total_area = width * height
    
    # 1. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use multiple thresholding methods to be robust
    thresholds = []
    
    # Adaptive thresholding
    thresh_adaptive = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    thresholds.append(thresh_adaptive)
    
    # Canny edge detection (RGB)
    canny = cv2.Canny(blurred, 50, 150)
    thresholds.append(canny)
    
    # Create list of (threshold_image, source_tag)
    threshold_data = []
    for thresh in thresholds:
        threshold_data.append((thresh, 'rgb'))
        
    # 2. Add Depth Edges if available
    if depth_map is not None:
        # Handle invalid depth (0, nan, inf)
        valid_mask = (depth_map > 0) & np.isfinite(depth_map)
        if np.any(valid_mask):
            d_min = np.min(depth_map[valid_mask])
            d_max = np.max(depth_map[valid_mask])
            
            if d_max > d_min:
                d_clean = depth_map.copy()
                d_clean[~valid_mask] = d_min # Fill invalid with floor
                
                # Normalize to 8-bit
                d_norm = ((d_clean - d_min) / (d_max - d_min) * 255).astype(np.uint8)
                
                # Denoise depth (slightly more aggressive as depth is often stepped)
                d_norm = cv2.medianBlur(d_norm, 5)
                d_canny = cv2.Canny(d_norm, 20, 60)
                
                # Add depth edges with higher priority tag
                threshold_data.append((d_canny, 'depth'))
    
    detections = []
    
    for thresh, source in threshold_data:
        # Morphological operations to close gaps
        kernel = np.ones((3,3), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        # 3. Find Contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            # 4. Filtering by Area
            area = cv2.contourArea(cnt)
            if area < total_area * min_area_ratio or area > total_area * max_area_ratio:
                continue
            
            # 5. Rectangularity Check
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int64(box)
            rect_area = rect[1][0] * rect[1][1]
            
            # Skip if it touches the image border
            x, y, w, h = cv2.boundingRect(box)
            if x <= 1 or y <= 1 or x + w >= width - 2 or y + h >= height - 2:
                continue

            rectangularity = area / (rect_area + 1e-6)
            
            if rectangularity > 0.6:
                # 6. Confidence Scoring
                score = calculate_rectangle_score(box, gray, rectangularity, depth_map, source == 'depth')
                
                detections.append({
                    'contour': box,
                    'score': score,
                    'area': area,
                    'source': source
                })

    # Sort by score, but give explicit priority to depth source
    # We do this by sorting by (is_depth, score)
    detections = sorted(detections, key=lambda x: (x['source'] == 'depth', x['score']), reverse=True)
    
    final_detections = []
    for d in detections:
        is_duplicate = False
        for f in final_detections:
            # Check for high IOU or central proximity
            # If one is inside another, we might want the inner or outer?
            # Usually the one with higher score is better.
            m1 = cv2.moments(d['contour'])
            m2 = cv2.moments(f['contour'])
            if m1['m00'] == 0 or m2['m00'] == 0: continue
            c1 = (int(m1['m10'] / m1['m00']), int(m1['m01'] / m1['m00']))
            c2 = (int(m2['m10'] / m2['m00']), int(m2['m01'] / m2['m00']))
            dist = np.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
            
            # If centroids are close (< 10% of image), consider them same object
            if dist < width * 0.1:
                is_duplicate = True
                break
        if not is_duplicate:
            final_detections.append(d)
            
    return final_detections

def calculate_rectangle_score(box_points, gray_img, rectangularity, depth_map=None, is_depth_source=False):
    """
    Calculates a confidence score based on:
    1. Orthogonality (how close angles are to 90 degrees)
    2. Aspect Ratio (penalize extreme ratios) 
    3. Edge strength along the box
    4. Rectangularity (contour area / box area)
    5. Depth consistency (Planarity + Elevation) - if depth_map provided
    6. Priority Boost - if detected from depth edges
    """
    pts = box_points.reshape(4, 2)
    
    # 1. Orthogonality
    ortho_score = 1.0 
    
    # 2. Aspect Ratio
    lengths = []
    for i in range(4):
        lengths.append(np.linalg.norm(pts[i] - pts[(i+1)%4]))
    aspect_ratio = max(lengths[0], lengths[1]) / (min(lengths[0], lengths[1]) + 1e-6)
    aspect_score = 1.0
    if aspect_ratio > 10:
        aspect_score = 0.5
    elif aspect_ratio > 20:
        aspect_score = 0.1
        
    # 3. Edge Strength
    mask = np.zeros(gray_img.shape, dtype=np.uint8)
    cv2.drawContours(mask, [box_points.astype(np.int32)], -1, 255, 1)
    
    sobelx = cv2.Sobel(gray_img, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray_img, cv2.CV_64F, 0, 1, ksize=3)
    mag = cv2.magnitude(sobelx, sobely)
    mag = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    edge_strength = np.mean(mag[mask == 255])
    edge_score = np.clip(edge_strength / 100.0, 0, 1)
    
    # 4. Rectangularity score
    rect_score = np.clip((rectangularity - 0.7) / 0.3, 0, 1)

    # 5. Depth Score
    depth_score = 0
    weights = {'ortho': 0.1, 'aspect': 0.1, 'edge': 0.3, 'rect': 0.5}
    
    if depth_map is not None:
        depth_score = calculate_depth_score(box_points, depth_map)
        # Shift weights if depth is available
        weights = {'ortho': 0.05, 'aspect': 0.05, 'edge': 0.2, 'rect': 0.3, 'depth': 0.4}
        final_score = (ortho_score * weights['ortho']) + \
                      (aspect_score * weights['aspect']) + \
                      (edge_score * weights['edge']) + \
                      (rect_score * weights['rect']) + \
                      (depth_score * weights['depth'])
    else:
        final_score = (ortho_score * weights['ortho']) + \
                      (aspect_score * weights['aspect']) + \
                      (edge_score * weights['edge']) + \
                      (rect_score * weights['rect'])
    
    # 6. Priority Boost for depth-derived detections
    if is_depth_source:
        final_score = np.clip(final_score * 1.5, 0, 1.0)
                      
    return float(final_score)

def main():
    parser = argparse.ArgumentParser(description="Rectangle detector using classical CV.")
    parser.add_argument(
        "--source", 
        type=Path, 
        default=Path("data/zed_snapshots"), 
        help="Path to input image or directory containing images."
    )
    parser.add_argument(
        "--output_dir", 
        type=Path, 
        default=Path("outputs/rectangle_detection"), 
        help="Directory to save results."
    )
    parser.add_argument(
        "--filter",
        type=str,
        default="",
        help="Phrase to filter filenames by (e.g., 'rgb')."
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search for images recursively in the source directory."
    )
    args = parser.parse_args()
    
    if not args.source.exists():
        print(f"Source not found: {args.source}")
        return

    # Find images
    if args.source.is_file():
        images = [args.source]
    else:
        if args.filter:
            pattern = f"*{args.filter}*"
        else:
            pattern = "*"
            
        if args.recursive:
            images = sorted(list(args.source.rglob(pattern)))
        else:
            images = sorted(list(args.source.glob(pattern)))
            
        # Filter for image extensions AND ensure we don't process depth files as primary inputs
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        images = [img for img in images if img.suffix.lower() in valid_exts 
                  and "depth" not in img.name.lower() 
                  and "_vis" not in img.name.lower()]

    if not images:
        print(f"No images found in {args.source} matching pattern.")
        return

    print(f"Found {len(images)} images. Processing...")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for img_path in images:
        print(f"Processing {img_path.name}...")
        
        # Look for depth map
        depth_map = load_depth_map(img_path)
        if depth_map is not None:
            print(f"  Found matching depth map for {img_path.name}")
            
        detections = detect_rectangles(img_path, depth_map=depth_map)
        
        # Visualize
        canvas = cv2.imread(str(img_path))
        if canvas is None:
            continue
            
        for d in detections:
            cv2.drawContours(canvas, [d['contour']], -1, (0, 255, 0), 3)
            # Put score
            x, y, w, h = cv2.boundingRect(d['contour'])
            cv2.putText(canvas, f"Score: {d['score']:.2f}", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
        out_path = output_dir / f"detected_{img_path.name}"
        cv2.imwrite(str(out_path), canvas)
        
    print(f"Done! Results saved to {output_dir}")

if __name__ == "__main__":
    main()

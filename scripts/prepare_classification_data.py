import os
import yaml
from pathlib import Path
import shutil

def prepare_classification_data(dataset_yaml_path, output_dir):
    """
    Creates a YOLO classification dataset structure from a detection dataset.
    Uses hard links to avoid duplicating image files.
    """
    with open(dataset_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    base_path = Path(data['path'])
    class_names = data['names']
    
    # Define splits to process
    splits = {
        'train': data.get('train', 'images/train'),
        'val': data.get('val', 'images/val'),
        'test': data.get('test', 'images/test')
    }
    
    output_base = Path(output_dir)
    print(f"Creating classification dataset at: {output_base}")
    
    for split_name, image_rel_path in splits.items():
        if not image_rel_path:
            continue
            
        img_dir = base_path / image_rel_path
        if not img_dir.exists():
            print(f"Warning: Image directory {img_dir} does not exist. Skipping {split_name}.")
            continue
            
        # Labels are assumed to be in a sibling 'labels' directory
        label_dir = base_path / 'labels' / Path(image_rel_path).name
        
        print(f"Processing {split_name} split...")
        
        count = 0
        for img_path in img_dir.glob('*'):
            if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.bmp']:
                continue
            
            # Find corresponding label file
            label_path = label_dir / (img_path.stem + '.txt')
            if not label_path.exists():
                continue
                
            # Read first class ID from detection label
            try:
                with open(label_path, 'r') as f:
                    line = f.readline().strip()
                    if not line:
                        continue
                    class_id = int(line.split()[0])
                    class_name = class_names[class_id]
            except (ValueError, IndexError, KeyError) as e:
                print(f"Error parsing {label_path}: {e}")
                continue
            
            # Sanitize class name for folder
            safe_class_name = str(class_name).replace(' ', '_').replace('/', '_')
            
            # Target path: output_dir/split/class_name/image.jpg
            target_dir = output_base / split_name / safe_class_name
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / img_path.name
            
            # Create hard link
            try:
                if target_path.exists():
                    os.remove(target_path)
                os.link(img_path, target_path)
                count += 1
            except OSError as e:
                print(f"Error linking {img_path} to {target_path}: {e}")
                # Fallback to copy if hard links fail (e.g., cross-device)
                shutil.copy2(img_path, target_path)
                count += 1
                
        print(f"Created {count} links for {split_name} split.")

if __name__ == "__main__":
    PROJECT_ROOT = Path(r"d:\..TUM course material\semester thisis\pcb computer vision")
    DATASET_YAML = PROJECT_ROOT / "yolo_dataset" / "dataset.yaml"
    OUTPUT_DIR = PROJECT_ROOT / "yolo_classification_dataset"
    
    prepare_classification_data(DATASET_YAML, OUTPUT_DIR)

import os
import json
import requests
import time
import ast
from openai import OpenAI

# Configuration
API_KEY = os.environ.get("OPENAI_API_KEY")
client = None


def extract_game_metadata():
    """Extract character types, item types, and other metadata from main.py"""
    metadata = {
        'characters': [],
        'items': {},
        'ui_elements': []
    }
    
    try:
        with open('main.py', 'r') as f:
            content = f.read()
            tree = ast.parse(content)
        
        # Find EntityType enum
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'EntityType':
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                enum_name = target.id
                                if enum_name not in ['PLAYER']:
                                    # Convert GRUMPY_GRANDMA to grumpy_grandma
                                    metadata['characters'].append(enum_name.lower())
        
        # Add player manually
        metadata['characters'].insert(0, 'player')
        
        # Find item types in spawn_items method
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'spawn_items':
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name) and target.id == 'item_types':
                                # Extract the list of tuples
                                if isinstance(child.value, ast.List):
                                    for elt in child.value.elts:
                                        if isinstance(elt, ast.Tuple) and len(elt.elts) >= 3:
                                            if isinstance(elt.elts[0], ast.Constant):
                                                item_type = elt.elts[0].value
                                                # Extract width and height from tuple
                                                if isinstance(elt.elts[2], ast.Constant):
                                                    size = elt.elts[2].value
                                                    metadata['items'][item_type] = size
        
        # UI elements (could extract from load_images but keep these standard)
        metadata['ui_elements'] = ['cart_obstacle', 'victory', 'defeat']
        
    except Exception as e:
        print(f"⚠️  Warning: Could not parse main.py: {e}")
        print("Using fallback metadata...")
        # Fallback
        metadata = {
            'characters': ['player', 'grumpy_grandma', 'speedy_grandpa', 'angry_karen', 'slow_larry'],
            'items': {'coin': 15, 'speed_boost': 10, 'energy_drink': 8},
            'ui_elements': ['cart_obstacle', 'victory', 'defeat']
        }
    
    return metadata

def generate_image(prompt, filename, force=False):
    """Generate an image with DALL-E 3 and save it"""
    global client
    
    if client is None:
        raise RuntimeError("OpenAI client not initialized. Set OPENAI_API_KEY environment variable.")
    
    full_path = f"images/{filename}"
    
    # Check if image already exists
    if os.path.exists(full_path) and not force:
        print(f"⏭️  {filename} already exists, skipping.")
        return True
    
    print(f"Generating {filename}...")
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download the image
        img_data = requests.get(image_url, verify=True).content
        with open(full_path, 'wb') as handler:
            handler.write(img_data)
        
        print(f"✅ {filename} created successfully!")
        
        # Delay to avoid overloading the API
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"❌ Error for {filename}: {e}")
        time.sleep(2)
        return False


# Consistent pixel art style context for all images
PIXEL_ART_STYLE = "16-bit pixel art style, retro video game graphics, crisp pixels with black outlines, vibrant colors, side view, classic arcade game aesthetic, sprite sheet quality"


def get_character_prompt(char_name):
    """Generate appropriate prompt for each character type"""
    prompts = {
        'player': f"A young energetic shopper in casual clothes running with a shopping cart, {PIXEL_ART_STYLE}, white background",
        'grumpy_grandma': f"A grumpy elderly woman with gray hair in a pink cardigan pushing a shopping cart, frowning face, {PIXEL_ART_STYLE}, white background",
        'speedy_grandpa': f"A fast elderly man with white hair in light blue clothes running with a shopping cart, determined expression, {PIXEL_ART_STYLE}, white background",
        'angry_karen': f"A middle-aged woman with orange clothes and a frustrated expression pushing a shopping cart quickly, determined face, {PIXEL_ART_STYLE}, white background",
        'slow_larry': f"A slow elderly man in tan/beige clothes with a shopping cart, relaxed expression, {PIXEL_ART_STYLE}, white background",
    }
    
    # Return specific prompt or generic one
    if char_name in prompts:
        return prompts[char_name]
    else:
        # Generic fallback for new characters
        char_display = char_name.replace('_', ' ').title()
        return f"A {char_display} character pushing a shopping cart, {PIXEL_ART_STYLE}, white background"


def get_item_prompt(item_name):
    """Generate appropriate prompt for each item type"""
    prompts = {
        'coin': f"A shiny golden coin with a dollar sign, glowing effect, {PIXEL_ART_STYLE}, white background",
        'speed_boost': f"A blue forward arrow icon with speed lines, glowing effect, power-up icon, {PIXEL_ART_STYLE}, white background",
        'energy_drink': f"A red energy drink can with lightning bolt symbol, {PIXEL_ART_STYLE}, white background",
    }
    
    if item_name in prompts:
        return prompts[item_name]
    else:
        # Generic fallback
        item_display = item_name.replace('_', ' ').title()
        return f"A {item_display} collectible item, {PIXEL_ART_STYLE}, white background"


def get_ui_prompt(ui_element):
    """Generate appropriate prompt for UI elements"""
    prompts = {
        'cart_obstacle': f"A gray metal shopping cart obstacle, {PIXEL_ART_STYLE}, white background",
        'victory': f"A golden trophy with confetti and stars, epic victory celebration banner, bright cheerful colors, {PIXEL_ART_STYLE}",
        'defeat': f"A sad face with dark clouds, game over screen element, somber colors, {PIXEL_ART_STYLE}",
    }
    
    if ui_element in prompts:
        return prompts[ui_element]
    else:
        element_display = ui_element.replace('_', ' ').title()
        return f"A {element_display} UI element, {PIXEL_ART_STYLE}"


def main():
    global client
    
    import sys
    dry_run = '--dry-run' in sys.argv or '--preview' in sys.argv
    force = '--force' in sys.argv or '-f' in sys.argv
    
    # Parse command line arguments for filtering
    filter_folder = None
    filter_name = None
    
    for arg in sys.argv[1:]:
        if arg.startswith('--folder='):
            filter_folder = arg.split('=')[1]
        elif arg.startswith('--name='):
            filter_name = arg.split('=')[1]
        elif not arg.startswith('--') and not arg.startswith('-'):
            # Assume it's a name if no prefix
            if '/' in arg or arg in ['characters', 'items', 'ui']:
                filter_folder = arg
            else:
                filter_name = arg
    
    if dry_run:
        print("🔍 DRY RUN MODE - No images will be generated\n")
    else:
        # Check for API key
        if not API_KEY:
            print("❌ Error: OPENAI_API_KEY environment variable is not set!")
            print("Set it with: export OPENAI_API_KEY='your-key-here'")
            print("\nTip: Run with --dry-run to preview what would be generated")
            exit(1)
        
        # Initialize client
        client = OpenAI(api_key=API_KEY)
    
    # Create image folders
    if not dry_run:
        os.makedirs("images", exist_ok=True)
        os.makedirs("images/characters", exist_ok=True)
        os.makedirs("images/backgrounds", exist_ok=True)
        os.makedirs("images/items", exist_ok=True)
        os.makedirs("images/ui", exist_ok=True)
    
    print("🎨 GENERATING IMAGES WITH DALL-E 3\n" if not dry_run else "")
    print("📖 Extracting metadata from main.py...")
    
    metadata = extract_game_metadata()
    
    print(f"✅ Found {len(metadata['characters'])} characters")
    print(f"✅ Found {len(metadata['items'])} item types")
    print(f"✅ Found {len(metadata['ui_elements'])} UI elements")
    
    # Show filter info
    if filter_folder:
        print(f"🔍 Filtering by folder: {filter_folder}")
    if filter_name:
        print(f"🔍 Filtering by name: {filter_name}")
    
    if dry_run:
        print(f"\n📋 Would generate the following images:")
        print(f"   - {len(metadata['characters'])} character sprites")
        print(f"   - 0 background elements (using procedural generation)")
        print(f"   - {len(metadata['items'])} item sprites")
        print(f"   - {len(metadata['ui_elements'])} UI elements")
        total = len(metadata['characters']) + len(metadata['items']) + len(metadata['ui_elements'])
        print(f"   Total: {total} images")
        print(f"\n💰 Cost savings: 3 fewer images (backgrounds use procedural generation)")
        return
    
    # 1. Character images
    if not filter_folder or filter_folder == 'characters':
        print("\n=== CHARACTERS ===")
        
        for char_name in metadata['characters']:
            if filter_name and char_name != filter_name:
                continue
            prompt = get_character_prompt(char_name)
            generate_image(prompt, f"characters/{char_name}.png", force)
    
    # 2. Background elements - SKIPPED
    # Using procedural backgrounds for perfect tiling and better performance
    if not filter_folder or filter_folder == 'backgrounds':
        print("\n\n=== BACKGROUNDS ===")
        print("⏭️  Skipping background generation - using procedural rendering for better tiling")
    
    # 3. Collectible items (dynamically from game)
    if not filter_folder or filter_folder == 'items':
        print("\n\n=== ITEMS ===")
        
        for item_name in metadata['items'].keys():
            if filter_name and item_name != filter_name:
                continue
            prompt = get_item_prompt(item_name)
            generate_image(prompt, f"items/{item_name}.png", force)
    
    # 4. UI elements (dynamically from game)
    if not filter_folder or filter_folder == 'ui':
        print("\n\n=== UI ELEMENTS ===")
        
        for ui_element in metadata['ui_elements']:
            if filter_name and ui_element != filter_name:
                continue
            prompt = get_ui_prompt(ui_element)
            generate_image(prompt, f"ui/{ui_element}.png", force)
    
    print("\n\n✨ GENERATION COMPLETE! ✨")
    print(f"All images are in the 'images/' folder")
    print("\nRun the game with: python main.py")


if __name__ == "__main__":
    import sys
    
    # Show help if requested
    if '--help' in sys.argv or '-h' in sys.argv:
        print("🎨 Mamitrax Image Generator")
        print("\nUsage:")
        print("  python generate_images.py [options]")
        print("\nOptions:")
        print("  --dry-run, --preview     Preview what would be generated without API calls")
        print("  --force, -f              Regenerate images even if they already exist")
        print("  --folder=<name>          Generate only images in specific folder")
        print("                           (characters, items, ui)")
        print("  --name=<name>            Generate only specific image by name")
        print("                           (e.g., player, angry_karen, coin)")
        print("  -h, --help               Show this help message")
        print("\nExamples:")
        print("  python generate_images.py --dry-run")
        print("  python generate_images.py --folder=characters")
        print("  python generate_images.py --name=player")
        print("  python generate_images.py characters")
        print("  python generate_images.py angry_karen")
        print("  python generate_images.py angry_karen --force")
        sys.exit(0)
    
    main()

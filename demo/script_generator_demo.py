import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from script_generator import generate_script_with_llm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_user_input():
    """Get script parameters from user input."""
    print("=== Video Script Generator Demo ===\n")
    
    # Get basic information
    brand_name = input("Enter your brand name: ").strip()
    if not brand_name:
        brand_name = "TechExplorer"
    
    we_focus_on = input("What does your brand focus on? ").strip()
    if not we_focus_on:
        we_focus_on = "making complex technology accessible to everyone"
    
    main_topic = input("Enter the main topic for your script: ").strip()
    if not main_topic:
        main_topic = "Artificial Intelligence"
    
    # Get key points
    print("\nEnter key points to cover (press Enter twice when done):")
    key_points = []
    while True:
        point = input("- ").strip()
        if not point:
            if key_points:  # If we have at least one point, break
                break
            else:  # If no points yet, provide default
                key_points = [
                    "What is AI and how does it work",
                    "Current applications in everyday life",
                    "Future possibilities and implications",
                    "Common misconceptions about AI"
                ]
                print("Using default key points:")
                for p in key_points:
                    print(f"- {p}")
                break
        key_points.append(point)
    
    # Get tone
    print("\nSelect tone:")
    print("1. Educational")
    print("2. Conversational") 
    print("3. Enthusiastic")
    print("4. Professional")
    print("5. Casual")
    
    tone_choice = input("Choose tone (1-5, default: 2): ").strip()
    tones = {
        "1": "educational",
        "2": "conversational",
        "3": "enthusiastic", 
        "4": "professional",
        "5": "casual"
    }
    tone = tones.get(tone_choice, "conversational")
    
    # Get target runtime
    try:
        runtime = int(input("Target runtime in minutes (default: 5): ") or "5")
    except ValueError:
        runtime = 5
    
    return brand_name, we_focus_on, main_topic, key_points, tone, runtime

def display_preset_options():
    """Display preset script options for quick testing."""
    presets = {
        "1": {
            "brand_name": "TechExplorer",
            "we_focus_on": "making complex technology accessible to everyone",
            "main_topic": "Renewable Energy Technologies",
            "key_points": [
                "Solar power advantages and technology",
                "Wind energy potential and challenges", 
                "Geothermal energy applications",
                "Future of renewable energy storage"
            ],
            "tone": "educational",
            "target_runtime": 6
        },
        "2": {
            "brand_name": "SpaceVoyager",
            "we_focus_on": "inspiring curiosity about space exploration",
            "main_topic": "Mars Exploration Mission",
            "key_points": [
                "Current Mars missions and discoveries",
                "Challenges of human Mars travel",
                "Technology needed for Mars colonization",
                "Timeline for future Mars missions"
            ],
            "tone": "enthusiastic", 
            "target_runtime": 8
        },
        "3": {
            "brand_name": "ClimateAction",
            "we_focus_on": "educating about climate change solutions",
            "main_topic": "Climate Change and Global Impact",
            "key_points": [
                "Evidence of climate change",
                "Major causes and contributors",
                "Impact on ecosystems and weather",
                "Individual and collective solutions"
            ],
            "tone": "professional",
            "target_runtime": 7
        }
    }
    
    print("=== Preset Script Options ===")
    for key, preset in presets.items():
        print(f"{key}. {preset['main_topic']} ({preset['tone']} tone, {preset['target_runtime']} min)")
        print(f"   Brand: {preset['brand_name']}")
        print(f"   Key points: {len(preset['key_points'])} topics")
        print()
    
    return presets

def main():
    """Main demo function."""
    try:
        print("Video Script Generator with AI Research\n")
        print("This demo will:")
        print("1. Research your topic using Wikipedia")
        print("2. Index research into ChromaDB knowledge base")
        print("3. Generate a script using AI with research backing")
        print("4. Save the script as a markdown file\n")
        
        # Ask for preset or custom input
        choice = input("Use preset (p) or enter custom parameters (c)? [p/c]: ").strip().lower()
        
        if choice == 'p':
            presets = display_preset_options()
            preset_choice = input("Select preset (1-3): ").strip()
            
            if preset_choice in presets:
                preset = presets[preset_choice]
                brand_name = preset["brand_name"]
                we_focus_on = preset["we_focus_on"] 
                main_topic = preset["main_topic"]
                key_points = preset["key_points"]
                tone = preset["tone"]
                target_runtime = preset["target_runtime"]
                
                print(f"\nUsing preset: {main_topic}")
            else:
                print("Invalid choice, using default parameters...")
                brand_name, we_focus_on, main_topic, key_points, tone, target_runtime = get_user_input()
        else:
            brand_name, we_focus_on, main_topic, key_points, tone, target_runtime = get_user_input()
        
        # Display summary
        print(f"\n=== Script Generation Summary ===")
        print(f"Brand: {brand_name}")
        print(f"Focus: {we_focus_on}")
        print(f"Topic: {main_topic}")
        print(f"Key Points: {len(key_points)}")
        for i, point in enumerate(key_points, 1):
            print(f"  {i}. {point}")
        print(f"Tone: {tone}")
        print(f"Target Runtime: {target_runtime} minutes")
        print()
        
        # Confirm before proceeding
        proceed = input("Generate script? [y/n]: ").strip().lower()
        if proceed != 'y':
            print("Script generation cancelled.")
            return
            
        print("\n" + "="*50)
        print("STARTING SCRIPT GENERATION")
        print("="*50)
        print("This may take a few minutes...")
        print()
        
        # Generate the script
        try:
            script = generate_script_with_llm(
                brand_name=brand_name,
                we_focus_on=we_focus_on,
                main_topic=main_topic,
                key_points=key_points,
                tone=tone,
                target_runtime=target_runtime
            )
            
            print("\n" + "="*50)
            print("SCRIPT GENERATION COMPLETED!")
            print("="*50)
            print("\nGenerated Script Preview:")
            print("-" * 30)
            
            # Show first 1000 characters of script
            script_preview = script[:1000] + "..." if len(script) > 1000 else script
            print(script_preview)
            
            print("\n" + "-" * 30)
            print(f"Full script saved to generated_scripts directory")
            print(f"Total length: {len(script)} characters")
            
            # Ask if user wants to see full script
            show_full = input("\nDisplay full script? [y/n]: ").strip().lower()
            if show_full == 'y':
                print("\n" + "="*50)
                print("FULL GENERATED SCRIPT")
                print("="*50)
                print(script)
            
        except Exception as e:
            print(f"\n❌ Error generating script: {e}")
            logger.error(f"Script generation failed: {e}")
            return
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Demo failed: {e}")

if __name__ == "__main__":
    main()
import json
import subprocess
import sys


def get_outdated_packages():
    """Fetches a list of outdated packages via pip in JSON format."""
    print("Checking for available package updates... Please wait.")
    try:
        # Runs 'pip list --outdated --format=json'
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse and return JSON data
        if result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error fetching outdated packages: {e.stderr}")
        return []


def upgrade_package(package_name):
    """Upgrades a specific package to its latest version."""
    try:
        print(f"Upgrading {package_name}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
            check=True,
        )
        print(f"Successfully upgraded {package_name}!\n")
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to upgrade {package_name}.\n")
        return False


def generate_requirements():
    """Generates a updated requirements.txt file."""
    print("Generating updated requirements.txt...")
    try:
        with open("requirements.txt", "w") as f:
            subprocess.run([sys.executable, "-m", "pip",
                           "freeze"], stdout=f, check=True)
        print("Successfully created 'requirements.txt' with updated versions!")
    except subprocess.CalledProcessError as e:
        print(f"Error generating requirements.txt: {e}")


def upgrade():
    outdated = get_outdated_packages()

    if not outdated:
        print("All your packages are already up to date!")
        # Optional: still generate requirements.txt if it doesn't exist
        generate_requirements()
        return

    print(f"\nFound {len(outdated)} package(s) with available updates:\n")

    updated_any = False

    for pkg in outdated:
        name = pkg.get("name")
        current_v = pkg.get("version")
        latest_v = pkg.get("latest_version")

        # Ask user for confirmation
        choice = (
            input(
                f"Update '{name}' from version {current_v} to {latest_v}? (y/N): "
            )
            .strip()
            .lower()
        )

        if choice in ["y", "yes"]:
            success = upgrade_package(name)
            if success:
                updated_any = True
        else:
            print(f"Skipped {name}.\n")

    # Always generate/refresh requirements.txt if the user made changes
    if updated_any:
        generate_requirements()
    else:
        print("No packages were updated. requirements.txt left unchanged.")


upgrade()

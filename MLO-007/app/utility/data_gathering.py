import os
import shutil


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
COPY_DIR = os.path.join(BASE_DIR, "MLO-007", "data")
print(f"Base directory: {BASE_DIR}")
print(f"Copy directory: {COPY_DIR}")


def collect_data():
    # Create COPY_DIR if it doesn't exist
    os.makedirs(COPY_DIR, exist_ok=True)
    # Placeholder for data collection logic
    for dir in os.listdir(BASE_DIR):
        dir_path = os.path.join(BASE_DIR, dir)
        if os.path.isdir(dir_path) and dir.startswith("MLO-"):
            for file in os.listdir(dir_path):
                if "README" in file:
                    shutil.copy(os.path.join(dir_path, file),
                                os.path.join(COPY_DIR, f"{dir}_README.md"))

if __name__ == "__main__":
    collect_data()
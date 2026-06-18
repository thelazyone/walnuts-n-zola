from .content import sync_all_folder_names
from .gui import run

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--sync-folders":
        changes = sync_all_folder_names()
        if changes:
            print("Renamed:")
            for line in changes:
                print(f"  {line}")
        else:
            print("All folder names already match titles.")
    else:
        run()

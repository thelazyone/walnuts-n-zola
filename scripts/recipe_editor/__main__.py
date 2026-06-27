from .content import configure_site_root, sync_all_folder_names
from .gui import run

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    root = None
    if "--root" in args:
        i = args.index("--root")
        if i + 1 >= len(args):
            raise SystemExit("--root requires a path")
        root = args[i + 1]
        del args[i : i + 2]

    configure_site_root(root)

    if args and args[0] == "--sync-folders":
        changes = sync_all_folder_names()
        if changes:
            print("Renamed:")
            for line in changes:
                print(f"  {line}")
        else:
            print("All folder names already match titles.")
    else:
        run()

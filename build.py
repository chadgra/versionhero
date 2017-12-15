"""
Build (freeze) the versionhero program.
"""
import os


def main():
    """
    Run this main function if this script is called directly.
    :return: None
    """
    os.system('pyinstaller --onefile versionhero.py')


if __name__ == "__main__":
    main()

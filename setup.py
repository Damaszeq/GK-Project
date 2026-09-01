import subprocess
import sys

def main():
    print("Installing required libraries for GK-Project...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\nInstallation complete! You can now run the game using 'python main.py'.")
    except subprocess.CalledProcessError:
        print("\nAn error occurred during installation. Please check the output above.")
    input("Press Enter to continue...")

if __name__ == '__main__':
    main()

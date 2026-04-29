import subprocess
import os

def copy_image_to_clipboard(file_path):
    # PowerShell command to copy image to clipboard
    abs_path = os.path.abspath(file_path)
    cmd = f"powershell -ExecutionPolicy Bypass -Command \"Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{abs_path}'))\""
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    # Test with a dummy image if exists or just check command syntax
    print("Testing image clipboard copy logic...")
    # copy_image_to_clipboard("test.jpg")

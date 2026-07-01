import os
import customtkinter
import PyInstaller.__main__

# Locate the customtkinter library directory to include its assets (themes, json files)
customtkinter_path = os.path.dirname(customtkinter.__file__)

PyInstaller.__main__.run([
    'app.py',                           # Your main application file
    '--noconfirm',                      # Overwrite output directory without asking
    '--windowed',                       # Hide the background console/terminal window
    '--onefile',                        # Bundle everything into a single .exe
    f'--add-data={customtkinter_path};customtkinter/', # Include CustomTkinter assets
    '--name=CorporateRAG'               # The name of the final executable
])
name: Build Windows Application

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build:
    runs-on: windows-latest

    steps:
      - name: Check out the repository
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyinstaller pillow tkinterdnd2 pymupdf

      - name: Download tkdnd
        run: |
          Invoke-WebRequest -Uri "https://sourceforge.net/projects/tkdnd/files/latest/download" -OutFile "tkdnd.zip"
          Expand-Archive -Path "tkdnd.zip" -DestinationPath "$env:USERPROFILE\tkdnd"
          Copy-Item -Path "$env:USERPROFILE\tkdnd\*" -Destination "$env:PYTHONPATH\tkdnd"

      - name: Build the application
        run: |
          pyinstaller --onefile --windowed pata9.py

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: Windows-app
          path: dist/pata9.exe

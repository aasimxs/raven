#!/bin/bash
echo "=================================================="
echo "        Raven - Setup (Linux/macOS)"
echo "=================================================="
echo ""

echo "[*] Setting up Python Backend..."
# Create venv in the root directory (matching list_dir output and raven.bat expectations)
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
cd backend
pip install -r requirements.txt
cd ..

echo ""
echo "[*] Setting up React Frontend..."
cd frontend
npm install
npm run build
cd ..

echo ""
echo "=================================================="
echo "[SUCCESS] Setup Complete! "
echo ""
echo "To start using Raven, you can now run:"
echo "  ./raven -help"
echo ""
echo "Note: Make sure to make the raven script executable via:"
echo "  chmod +x raven"
echo "=================================================="

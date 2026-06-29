@echo off
cd /d "%~dp0"
echo Starting bilingual translation server...
echo Open http://127.0.0.1:8910/ in your browser
start "" http://127.0.0.1:8910/index.html
python -m http.server 8910 --bind 127.0.0.1

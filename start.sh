#!/bin/bash
set -e

echo "==========================================="
echo "   Iniciando Ermis - Tradutor de Vídeo     "
echo "==========================================="

echo ""
echo "[1/3] Limpando portas e processos antigos..."
fuser -k -9 7000/tcp 2>/dev/null || true
fuser -k -9 8082/tcp 2>/dev/null || true
pkill -f "python app.py" 2>/dev/null || true
pkill -f "litserve" 2>/dev/null || true


export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo ""
echo "[2/3] Compilando e iniciando o Frontend React (Porta 8082)..."
cd frontend_react
npm run build

# Inicia o servidor estático em backgroung na porta 8082 usando pacote serve do NPM
npx --yes serve -s dist -l 8082 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✓ Frontend rodando na porta 8082. Acesse: http://localhost:8082"

echo ""
echo "[3/3] Iniciando o Servidor Backend FastAPI (Porta 7000)..."
echo "✓ Backend rodando na porta 7000."
echo "==========================================="

# Garante que dependências estejam instaladas
pip install -r requirements.txt > /dev/null 2>&1 || true

# Inicializa o Python no processo atual
python app.py

# Caso o python seja parado pelo usuário (Ctrl+C), mata o script do frontend também
kill $FRONTEND_PID 2>/dev/null || true

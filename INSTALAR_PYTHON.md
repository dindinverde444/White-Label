# 🐍 Como Instalar Python no Windows

## 📋 Passo a Passo Detalhado

### 1. Baixar Python
1. Acesse: https://www.python.org/downloads/
2. Clique no botão amarelo "Download Python 3.x.x"
3. Aguarde o download completar

### 2. Instalar Python
1. **Execute o arquivo baixado** (ex: python-3.11.x-amd64.exe)
2. **IMPORTANTE**: Na primeira tela, **marque a caixa "Add Python to PATH"**
3. Clique em "Install Now"
4. Aguarde a instalação completar
5. Clique em "Close"

### 3. Verificar a Instalação
Abra um **novo** terminal (PowerShell ou CMD) e digite:

```bash
python --version
```

Se funcionar, você verá algo como: `Python 3.11.x`

### 4. Testar o Gateway Python
```bash
python gateway.py
```

## 🚨 Problemas Comuns

### Python não encontrado:
1. **Reinicie o terminal** após a instalação
2. Tente: `py --version` em vez de `python --version`
3. Verifique se marcou "Add Python to PATH" durante a instalação

### Se ainda não funcionar:
1. Desinstale o Python
2. Baixe novamente do site oficial
3. Durante a instalação, **certifique-se de marcar "Add Python to PATH"**
4. Reinicie o computador

## ✅ Verificação Final

Após instalar, execute:

```bash
# Verificar versão
python --version

# Testar o gateway
python gateway.py
```

## 🎯 Resultado Esperado

Você deve ver algo como:
```
🚀 INICIANDO GATEWAY SIMPLES
==================================================
🚪 Gateway iniciado com sucesso!
📋 Serviços disponíveis:
   - usuario: http://localhost:3001
   - produto: http://localhost:3002
   - pedido: http://localhost:3003
```

## 📞 Precisa de Ajuda?

Se ainda tiver problemas:
1. Verifique se baixou do site oficial (python.org)
2. Certifique-se de marcar "Add Python to PATH"
3. Reinicie o terminal após a instalação
4. Tente reiniciar o computador

---

**Dica**: O Python é muito útil para programação! Vale a pena configurar corretamente! 🚀

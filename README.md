# 🚪 Gateway Simples

## O que é um Gateway?

Imagine um **porteiro de prédio**:
- Ele recebe visitantes
- Verifica se eles têm autorização
- Direciona cada um para o lugar certo
- Mantém um registro de quem entrou e saiu

Um **Gateway** funciona exatamente assim, mas para sistemas de computador!

## 🎯 O que este projeto faz?

Este é um gateway simples que:
- ✅ Recebe requisições (pedidos)
- ✅ Valida se são válidas
- ✅ Direciona para os serviços corretos
- ✅ Registra tudo que acontece
- ✅ Mostra estatísticas

## 🚀 Como usar?

### 1. Instalar Python
Certifique-se de ter Python instalado no seu computador.

### 2. Executar o Gateway
```bash
python gateway.py
```

### 3. Ver o resultado
O programa vai mostrar:
- Como o gateway inicia
- Como processa diferentes tipos de requisições
- Estatísticas finais

## 📚 Explicação do Código

### Estrutura Principal
```python
class GatewaySimples:
    def __init__(self):        # Inicialização
    def registrar_requisicao(): # Registra entradas/saídas
    def validar_requisicao():  # Verifica se é válido
    def processar_requisicao(): # Processa a requisição
    def mostrar_estatisticas(): # Mostra relatórios
```

### Como funciona?
1. **Recebe** uma requisição
2. **Registra** no histórico
3. **Valida** se é válida
4. **Processa** e encaminha
5. **Retorna** a resposta

## 🧪 Exemplos de Teste

O programa testa 4 cenários:
1. ✅ Requisição para serviço "usuario"
2. ✅ Requisição para serviço "produto"  
3. ✅ Requisição para serviço "pedido"
4. ❌ Requisição para serviço inexistente (testa tratamento de erro)

## 📊 O que você vai aprender?

- **Conceitos básicos** de programação
- **Como funciona** um gateway
- **Validação de dados**
- **Tratamento de erros**
- **Registro de logs**
- **Estruturas de dados** (dicionários, listas)

## 🎓 Para Iniciantes

Este código foi feito pensando em quem está começando:
- Comentários explicativos em português
- Analogias simples (porteiro)
- Estrutura clara e organizada
- Exemplos práticos

## 🔧 Próximos Passos

Depois de entender este gateway básico, você pode:
- Adicionar mais validações
- Conectar com serviços reais
- Criar uma interface web
- Adicionar autenticação
- Implementar cache

## 📝 Licença

Este projeto é educacional e pode ser usado livremente para aprender!

---

**Dica**: Execute o código e observe cada linha de saída. Isso vai te ajudar a entender como cada parte funciona! 🚀

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway Simples - Um "Portão" para Gerenciar Requisições

O que é um Gateway?
- É como um porteiro de um prédio que decide para onde direcionar as pessoas
- Recebe pedidos (requisições) e os encaminha para os lugares certos
- Pode fazer verificações de segurança antes de deixar passar
"""

import json
import time
from datetime import datetime

class GatewaySimples:
    """
    Classe principal do nosso Gateway
    Pense nela como o "cérebro" do nosso porteiro
    """
    
    def __init__(self):
        """
        Construtor - é executado quando criamos um novo gateway
        Aqui definimos as configurações iniciais
        """
        # Lista de serviços que nosso gateway conhece
        self.servicos = {
            "usuario": "http://localhost:3001",
            "produto": "http://localhost:3002", 
            "pedido": "http://localhost:3003"
        }
        
        # Histórico de requisições (como um livro de registro)
        self.historico = []
        
        # Contador de requisições
        self.contador_requisicoes = 0
        
        print("🚪 Gateway iniciado com sucesso!")
        print("📋 Serviços disponíveis:")
        for nome, url in self.servicos.items():
            print(f"   - {nome}: {url}")
    
    def registrar_requisicao(self, tipo, dados):
        """
        Registra cada requisição que passa pelo gateway
        Como um porteiro anotando quem entrou e saiu
        """
        registro = {
            "id": self.contador_requisicoes + 1,
            "tipo": tipo,
            "dados": dados,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.historico.append(registro)
        self.contador_requisicoes += 1
        
        print(f"📝 Registrado: {tipo} - {dados}")
    
    def validar_requisicao(self, dados):
        """
        Verifica se a requisição é válida
        Como um porteiro verificando documentos
        """
        # Verifica se tem dados
        if not dados:
            return False, "Dados vazios"
        
        # Verifica se tem tipo de serviço
        if "tipo" not in dados:
            return False, "Tipo de serviço não especificado"
        
        # Verifica se o serviço existe
        if dados["tipo"] not in self.servicos:
            return False, f"Serviço '{dados['tipo']}' não encontrado"
        
        return True, "Requisição válida"
    
    def processar_requisicao(self, dados):
        """
        Processa uma requisição
        É o trabalho principal do nosso gateway
        """
        print(f"\n🔄 Processando requisição...")
        
        # 1. Registra a requisição
        self.registrar_requisicao("entrada", dados)
        
        # 2. Valida a requisição
        valido, mensagem = self.validar_requisicao(dados)
        
        if not valido:
            print(f"❌ Erro: {mensagem}")
            return {"erro": mensagem}
        
        # 3. Simula o processamento (em um gateway real, aqui faria a requisição real)
        tipo_servico = dados["tipo"]
        url_servico = self.servicos[tipo_servico]
        
        print(f"✅ Requisição válida!")
        print(f"📤 Encaminhando para: {url_servico}")
        
        # Simula um delay de processamento
        time.sleep(1)
        
        # 4. Simula resposta do serviço
        resposta = {
            "status": "sucesso",
            "servico": tipo_servico,
            "url": url_servico,
            "mensagem": f"Dados processados pelo serviço {tipo_servico}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 5. Registra a resposta
        self.registrar_requisicao("saida", resposta)
        
        return resposta
    
    def mostrar_estatisticas(self):
        """
        Mostra estatísticas do gateway
        Como um relatório do porteiro
        """
        print(f"\n📊 ESTATÍSTICAS DO GATEWAY")
        print(f"   Total de requisições: {self.contador_requisicoes}")
        print(f"   Serviços disponíveis: {len(self.servicos)}")
        print(f"   Histórico de registros: {len(self.historico)}")
        
        if self.historico:
            print(f"\n📋 ÚLTIMAS 5 REQUISIÇÕES:")
            for registro in self.historico[-5:]:
                print(f"   [{registro['timestamp']}] {registro['tipo']}: {registro['dados']}")

def main():
    """
    Função principal - onde tudo começa
    """
    print("🚀 INICIANDO GATEWAY SIMPLES")
    print("=" * 50)
    
    # Cria um novo gateway
    gateway = GatewaySimples()
    
    # Exemplos de requisições para testar
    exemplos = [
        {"tipo": "usuario", "acao": "criar", "nome": "João Silva"},
        {"tipo": "produto", "acao": "listar", "categoria": "eletronicos"},
        {"tipo": "pedido", "acao": "buscar", "id": "12345"},
        {"tipo": "servico_inexistente", "acao": "teste"},  # Este vai dar erro
    ]
    
    print(f"\n🧪 TESTANDO O GATEWAY")
    print("=" * 50)
    
    # Processa cada exemplo
    for i, exemplo in enumerate(exemplos, 1):
        print(f"\n--- Teste {i} ---")
        resultado = gateway.processar_requisicao(exemplo)
        print(f"Resultado: {resultado}")
    
    # Mostra estatísticas finais
    gateway.mostrar_estatisticas()
    
    print(f"\n✅ Gateway funcionando perfeitamente!")
    print("🎉 Parabéns! Você criou seu primeiro gateway!")

if __name__ == "__main__":
    main()

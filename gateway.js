/**
 * Gateway Simples em JavaScript
 * 
 * O que é um Gateway?
 * - É como um porteiro de um prédio que decide para onde direcionar as pessoas
 * - Recebe pedidos (requisições) e os encaminha para os lugares certos
 * - Pode fazer verificações de segurança antes de deixar passar
 */

class GatewaySimples {
    /**
     * Construtor - é executado quando criamos um novo gateway
     * Aqui definimos as configurações iniciais
     */
    constructor() {
        // Lista de serviços que nosso gateway conhece
        this.servicos = {
            "usuario": "http://localhost:3001",
            "produto": "http://localhost:3002", 
            "pedido": "http://localhost:3003"
        };
        
        // Histórico de requisições (como um livro de registro)
        this.historico = [];
        
        // Contador de requisições
        this.contadorRequisicoes = 0;
        
        console.log("🚪 Gateway iniciado com sucesso!");
        console.log("📋 Serviços disponíveis:");
        for (let [nome, url] of Object.entries(this.servicos)) {
            console.log(`   - ${nome}: ${url}`);
        }
    }
    
    /**
     * Registra cada requisição que passa pelo gateway
     * Como um porteiro anotando quem entrou e saiu
     */
    registrarRequisicao(tipo, dados) {
        const registro = {
            id: this.contadorRequisicoes + 1,
            tipo: tipo,
            dados: dados,
            timestamp: new Date().toLocaleString('pt-BR')
        };
        
        this.historico.push(registro);
        this.contadorRequisicoes++;
        
        console.log(`📝 Registrado: ${tipo} - ${JSON.stringify(dados)}`);
    }
    
    /**
     * Verifica se a requisição é válida
     * Como um porteiro verificando documentos
     */
    validarRequisicao(dados) {
        // Verifica se tem dados
        if (!dados || Object.keys(dados).length === 0) {
            return { valido: false, mensagem: "Dados vazios" };
        }
        
        // Verifica se tem tipo de serviço
        if (!dados.tipo) {
            return { valido: false, mensagem: "Tipo de serviço não especificado" };
        }
        
        // Verifica se o serviço existe
        if (!this.servicos[dados.tipo]) {
            return { valido: false, mensagem: `Serviço '${dados.tipo}' não encontrado` };
        }
        
        return { valido: true, mensagem: "Requisição válida" };
    }
    
    /**
     * Processa uma requisição
     * É o trabalho principal do nosso gateway
     */
    async processarRequisicao(dados) {
        console.log(`\n🔄 Processando requisição...`);
        
        // 1. Registra a requisição
        this.registrarRequisicao("entrada", dados);
        
        // 2. Valida a requisição
        const validacao = this.validarRequisicao(dados);
        
        if (!validacao.valido) {
            console.log(`❌ Erro: ${validacao.mensagem}`);
            return { erro: validacao.mensagem };
        }
        
        // 3. Simula o processamento (em um gateway real, aqui faria a requisição real)
        const tipoServico = dados.tipo;
        const urlServico = this.servicos[tipoServico];
        
        console.log(`✅ Requisição válida!`);
        console.log(`📤 Encaminhando para: ${urlServico}`);
        
        // Simula um delay de processamento
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 4. Simula resposta do serviço
        const resposta = {
            status: "sucesso",
            servico: tipoServico,
            url: urlServico,
            mensagem: `Dados processados pelo serviço ${tipoServico}`,
            timestamp: new Date().toLocaleString('pt-BR')
        };
        
        // 5. Registra a resposta
        this.registrarRequisicao("saida", resposta);
        
        return resposta;
    }
    
    /**
     * Mostra estatísticas do gateway
     * Como um relatório do porteiro
     */
    mostrarEstatisticas() {
        console.log(`\n📊 ESTATÍSTICAS DO GATEWAY`);
        console.log(`   Total de requisições: ${this.contadorRequisicoes}`);
        console.log(`   Serviços disponíveis: ${Object.keys(this.servicos).length}`);
        console.log(`   Histórico de registros: ${this.historico.length}`);
        
        if (this.historico.length > 0) {
            console.log(`\n📋 ÚLTIMAS 5 REQUISIÇÕES:`);
            const ultimas = this.historico.slice(-5);
            ultimas.forEach(registro => {
                console.log(`   [${registro.timestamp}] ${registro.tipo}: ${JSON.stringify(registro.dados)}`);
            });
        }
    }
}

/**
 * Função principal - onde tudo começa
 */
async function main() {
    console.log("🚀 INICIANDO GATEWAY SIMPLES");
    console.log("=".repeat(50));
    
    // Cria um novo gateway
    const gateway = new GatewaySimples();
    
    // Exemplos de requisições para testar
    const exemplos = [
        { tipo: "usuario", acao: "criar", nome: "João Silva" },
        { tipo: "produto", acao: "listar", categoria: "eletronicos" },
        { tipo: "pedido", acao: "buscar", id: "12345" },
        { tipo: "servico_inexistente", acao: "teste" },  // Este vai dar erro
    ];
    
    console.log(`\n🧪 TESTANDO O GATEWAY`);
    console.log("=".repeat(50));
    
    // Processa cada exemplo
    for (let i = 0; i < exemplos.length; i++) {
        const exemplo = exemplos[i];
        console.log(`\n--- Teste ${i + 1} ---`);
        const resultado = await gateway.processarRequisicao(exemplo);
        console.log(`Resultado: ${JSON.stringify(resultado, null, 2)}`);
    }
    
    // Mostra estatísticas finais
    gateway.mostrarEstatisticas();
    
    console.log(`\n✅ Gateway funcionando perfeitamente!`);
    console.log("🎉 Parabéns! Você criou seu primeiro gateway!");
}

// Executa o programa
main().catch(console.error);

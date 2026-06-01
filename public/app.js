document.addEventListener("DOMContentLoaded", () => {
    
    // DETECTOR DE AMBIENTE: Identifica se é local (computador) ou produção (Vercel)
    // Detecta se estamos rodando localmente na porta 5000
    const baseUrl = (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") 
        ? "http://127.0.0.1:5000" 
        : ""; // Se não for local, ele usa o caminho relativo (funciona no Render!)

    // ==========================================
    // LÓGICA DA TELA DE LOGIN
    // ==========================================
    const formLogin = document.getElementById("formLogin");
    
    if (formLogin) {
        formLogin.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const usuario = document.getElementById("usuario").value;
            const senha = document.getElementById("senha").value;
            
            try {
                const response = await fetch(`${baseUrl}/api/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ usuario: usuario, senha: senha })
                });
                
                if (response.ok) {
                    window.location.href = "pedidos.html";
                } else {
                    alert("Usuário ou senha incorretos!");
                }
            } catch (error) {
                console.error("Erro:", error);
                alert("Erro de comunicação com o servidor.");
            }
        });
    }
    
    // ==========================================
    // LÓGICA DA TELA DE PEDIDOS
    // ==========================================
    const formPedido = document.getElementById("formPedido");
    const inputTelefone = document.getElementById("telefone");

    if (inputTelefone && localStorage.getItem("telefoneSalvo")) {
        inputTelefone.value = localStorage.getItem("telefoneSalvo");
    }

    if (formPedido) {
        formPedido.addEventListener("submit", async (e) => {
            e.preventDefault();
            const telefone = document.getElementById("telefone").value;
            const produto = document.getElementById("produto").value;
            const quantidade = document.getElementById("quantidade").value;
            const setor = document.getElementById("setor").value;

            const payload = {
                telefone: telefone,
                produto: produto,
                quantidade: parseInt(quantidade),
                setor_destino: setor
            };

            try {
                const response = await fetch(`${baseUrl}/api/pedidos`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    localStorage.setItem("telefoneSalvo", telefone);

                    const mensagem = `*Novo Pedido Solicitado!*\n\n📍 *Destino:* ${setor}\n📦 *Item:* ${produto}\n🔢 *Quantidade:* ${quantidade}\n\nO seu pedido já foi recebido pelo sistema e está em fase de processamento.`;
                    const linkWhatsapp = `https://wa.me/55${telefone.replace(/\D/g, '')}?text=${encodeURIComponent(mensagem)}`;
                    
                    window.open(linkWhatsapp, '_blank');
                    
                    formPedido.reset();
                    document.getElementById("telefone").value = localStorage.getItem("telefoneSalvo");
                }
            } catch (error) {
                console.error("Erro:", error);
            }
        });
    }

    // ==========================================
    // LÓGICA DO PAINEL DE RENDERS & GRÁFICOS
    // ==========================================
    const dashTotal = document.getElementById("dashTotal");
    const btnPreview = document.getElementById("btnPreview");
    const btnExportar = document.getElementById("btnExportar");
    const tabelaBody = document.querySelector("#tabelaPreview tbody");

    let chartProdutosInstance = null;
    let chartSetoresInstance = null;

    function renderizarGraficosVisuais(dados) {
        const resumoProdutos = { 'agua': 0, 'gás': 0, 'caminhão pipa': 0 };
        const resumoSetores = {};

        dados.forEach(p => {
            const prod = p.produto ? p.produto.toLowerCase() : '';
            const setor = p.setor_destino || 'Não Informado';
            const qtd = parseInt(p.quantidade) || 0;

            if (prod in resumoProdutos) resumoProdutos[prod] += qtd;
            resumoSetores[setor] = (resumoSetores[setor] || 0) + qtd;
        });

        const ctxProd = document.getElementById('chartProdutos').getContext('2d');
        if (chartProdutosInstance) chartProdutosInstance.destroy();
        chartProdutosInstance = new Chart(ctxProd, {
            type: 'doughnut',
            data: {
                labels: ['Água', 'Gás', 'Caminhão Pipa'],
                datasets: [{
                    data: [resumoProdutos['agua'], resumoProdutos['gás'], resumoProdutos['caminhão pipa']],
                    backgroundColor: ['#007bff', '#ffc107', '#17a2b8']
                }]
            },
            options: { responsive: true, plugins: { title: { display: true, text: 'Volume por Produto' } } }
        });

        const ctxSetor = document.getElementById('chartSetores').getContext('2d');
        if (chartSetoresInstance) chartSetoresInstance.destroy();
        chartSetoresInstance = new Chart(ctxSetor, {
            type: 'bar',
            data: {
                labels: Object.keys(resumoSetores),
                datasets: [{
                    label: 'Quantidade',
                    data: Object.values(resumoSetores),
                    backgroundColor: '#28a745'
                }]
            },
            options: { responsive: true, plugins: { title: { display: true, text: 'Demandas por Setor' } } }
        });
    }

    async function inicializarPainel() {
        try {
            const resDash = await fetch(`${baseUrl}/api/dashboard`);
            const dadosDash = await resDash.json();
            if (resDash.ok) {
                document.getElementById("dashTotal").innerText = dadosDash.total;
                document.getElementById("dashMes").innerText = dadosDash.envios_mes;
                document.getElementById("dashDemanda").innerText = dadosDash.maior_demanda;
            }

            const resPedidos = await fetch(`${baseUrl}/api/pedidos`);
            const dadosPedidos = await resPedidos.json();
            if (resPedidos.ok) {
                renderizarGraficosVisuais(dadosPedidos);
                atualizarTabelaHtml(dadosPedidos);
            }
        } catch (error) {
            console.error("Erro ao iniciar painel:", error);
        }
    }

    function atualizarTabelaHtml(dados) {
        tabelaBody.innerHTML = "";
        if (dados.length === 0) {
            tabelaBody.innerHTML = "<tr><td colspan='5' style='text-align:center;'>Nenhum resultado para o filtro aplicado.</td></tr>";
            return;
        }
        dados.forEach(pedido => {
            const dataFormatada = new Date(pedido.data_criacao).toLocaleDateString('pt-BR');
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${dataFormatada}</td>
                <td>${pedido.telefone}</td>
                <td>${pedido.produto}</td>
                <td>${pedido.quantidade}</td>
                <td>${pedido.setor_destino}</td>
            `;
            tabelaBody.appendChild(tr);
        });
    }

    function montarUrlComFiltros(baseUrlDefinida) {
        const inputData = document.getElementById("filtroData");
        const inputMes = document.getElementById("filtroMes"); // <- Pega o novo campo de Mês
        const selectProduto = document.getElementById("filtroProduto");
        
        const params = new URLSearchParams();
        
        // Se preencheu o Dia, adiciona na URL
        if (inputData && inputData.value) params.append("data", inputData.value);
        
        // Se preencheu o Mês, adiciona na URL
        if (inputMes && inputMes.value) params.append("mes", inputMes.value);
        
        // Se escolheu Produto, adiciona na URL
        if (selectProduto && selectProduto.value) params.append("produto", selectProduto.value);
        
        const query = params.toString();
        return query ? `${baseUrlDefinida}?${query}` : baseUrlDefinida;
    }

    if (btnPreview) {
        btnPreview.addEventListener("click", async () => {
            try {
                const url = montarUrlComFiltros(`${baseUrl}/api/pedidos`);
                const response = await fetch(url);
                const dados = await response.json();
                if (response.ok) {
                    renderizarGraficosVisuais(dados);
                    atualizarTabelaHtml(dados);
                }
            } catch (error) {
                console.error(error);
            }
        });
    }

    if (btnExportar) {
        btnExportar.addEventListener("click", () => {
            window.location.href = montarUrlComFiltros(`${baseUrl}/api/exportar`);
        });
    }

    if (dashTotal) {
        inicializarPainel();
    }
});
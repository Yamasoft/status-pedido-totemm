let empresa_id = null;
let carrinho = [];

/* ─────────── Carregar Categorias ─────────── */
function carregarCategorias() {
    const urlParams = new URLSearchParams(window.location.search);
    empresa_id = urlParams.get("empresa_id") || window.EMPRESA_ID;

    if (!empresa_id) {
        console.error("empresa_id não encontrado na URL");
        return;
    }

    fetch('/categorias/' + empresa_id)
        .then(res => res.json())
        .then(categorias => {
            const container = document.getElementById('categorias');
            container.innerHTML = '';
            categorias.forEach(cat => {
                const btn = document.createElement('button');
                btn.innerText = cat.nome;

                btn.onclick = () => {
                    document.querySelectorAll('#categorias button').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    carregarProdutos(cat.id);
                };

                container.appendChild(btn);
            });
        });
}

/* ─────────── Carregar Produtos ─────────── */
function carregarProdutos(grupo_id) {
    fetch('/produtos/' + grupo_id)
        .then(res => res.json())
        .then(produtos => {
            const container = document.getElementById('produtos');
            container.innerHTML = '';

            produtos.forEach(prod => {
                const card = document.createElement('div');
                card.className = 'produto-card';
                card.onclick = () => adicionarAoCarrinho(prod);

                const img = document.createElement('img');
                img.src = prod.foto || '/static/frontend/sem_foto.png';
                img.alt = prod.nome;
                card.appendChild(img);

                const nome = document.createElement('h3');
                nome.innerText = prod.nome;
                card.appendChild(nome);

                const preco = document.createElement('p');
                preco.innerText = `R$ ${prod.preco.toFixed(2)}`;
                card.appendChild(preco);

                container.appendChild(card);
            });
        });
}

/* ─────────── Carrinho ─────────── */
function carregarCarrinhoSalvo() {
    let carrinhoSalvo = localStorage.getItem('carrinho_itens');
    if (carrinhoSalvo) {
        try {
            carrinho = JSON.parse(carrinhoSalvo);
            atualizarCarrinho();
        } catch (e) {
            console.error('Erro ao ler carrinho salvo:', e);
        }
    }
}

function adicionarAoCarrinho(produto) {
    const existe = carrinho.find(p => p.id === produto.id);
    if (existe) {
        existe.quantidade++;
    } else {
        carrinho.push({ ...produto, quantidade: 1 });
    }
    atualizarCarrinho();
}

function alterarQtd(id, delta) {
    const item = carrinho.find(p => p.id === id);
    if (!item) return;
    item.quantidade += delta;
    if (item.quantidade <= 0) {
        carrinho = carrinho.filter(p => p.id !== id);
    }
    atualizarCarrinho();
}

function removerItem(id) {
    carrinho = carrinho.filter(p => p.id !== id);
    atualizarCarrinho();
}

function atualizarCarrinho() {
    const container = document.getElementById('itens-carrinho');
    container.innerHTML = '';
    let total = 0;

    carrinho.forEach(item => {
        total += item.preco * item.quantidade;

        const linha = document.createElement('div');
        linha.className = 'item-linha';
        linha.innerHTML = `
            <div class="botoes-qtd">
                <button class="lixeira" onclick="removerItem(${item.id})">🗑️</button>
                <button onclick="alterarQtd(${item.id}, -1)">-</button>
                <span>${item.quantidade}</span>
                <button onclick="alterarQtd(${item.id}, 1)">+</button>
            </div>
            <span class="desc">${item.nome}</span>
            <span class="preco">R$ ${(item.preco * item.quantidade).toFixed(2)}</span>
        `;
        container.prepend(linha);
    });

    document.getElementById('total-pedido').innerText = 'Total: R$ ' + total.toFixed(2);
}

/* ─────────── Ir para Pagamento ─────────── */
function irParaPagamento() {
    let total = 0;
    carrinho.forEach(item => {
        total += item.preco * item.quantidade;
    });

    if (total === 0 || carrinho.length === 0) {
        exibirAviso("⚠️ Nenhum item selecionado", "Por favor, escolha ao menos um produto antes de continuar.");
        return;
    }

    localStorage.setItem('total_carrinho', total.toFixed(2));
    localStorage.setItem('carrinho_itens', JSON.stringify(carrinho));
    window.location.href = "/pagamento?empresa_id=" + empresa_id + "&total=" + total.toFixed(2);
}

/* ─────────── Cancelar Pedido ─────────── */
function cancelarPedido() {
    carrinho = [];
    localStorage.removeItem('carrinho_itens');
    localStorage.removeItem('total_carrinho');
    window.location.href = "/empresas_web";
}

/* ─────────── Aviso visual elegante ─────────── */
function exibirAviso(titulo, mensagem) {
    const div = document.createElement("div");
    div.style.cssText = `
        position: fixed;
        top: 20%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #FFF3E0;
        border: 3px solid #FF9800;
        color: #BF360C;
        padding: 24px 30px;
        font-size: 22px;
        font-weight: bold;
        border-radius: 12px;
        box-shadow: 0 0 20px rgba(0,0,0,0.2);
        z-index: 9999;
        text-align: center;
        max-width: 90%;
    `;
    div.innerHTML = `<div>${titulo}</div><div style="font-size:18px; font-weight:normal; margin-top:10px;">${mensagem}</div>`;
    document.body.appendChild(div);

    setTimeout(() => {
        div.remove();
    }, 4000);
}

window.onload = () => {
    carregarCategorias();
    carregarCarrinhoSalvo();
};

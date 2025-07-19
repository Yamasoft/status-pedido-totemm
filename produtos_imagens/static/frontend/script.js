
let empresa_id = null;
let carrinho = [];

function carregarCategorias() {
    const urlParams = new URLSearchParams(window.location.search);
    empresa_id = urlParams.get("empresa_id");
    if (!empresa_id) return;

    fetch('/categorias/' + empresa_id)
        .then(res => res.json())
        .then(categorias => {
            const container = document.getElementById('categorias');
            container.innerHTML = '';
            categorias.forEach(cat => {
                const btn = document.createElement('button');
                btn.innerText = cat.nome;
                btn.onclick = () => carregarProdutos(cat.id);
                container.appendChild(btn);
            });
        });
}

function carregarProdutos(grupo_id) {
    fetch('/produtos/' + grupo_id)
        .then(res => res.json())
        .then(produtos => {
            const container = document.getElementById('produtos');
            container.innerHTML = '';
            produtos.forEach(prod => {
                const card = document.createElement('div');
                card.className = 'produto';

                // ✅ AQUI: Caminho para as imagens
                const img = document.createElement('img');
                img.src = '/static/imagens/' + prod.foto;
                img.alt = prod.nome;
                img.style.cursor = "pointer";  // deixa o mouse com "mãozinha"
                img.onclick = () => adicionarAoCarrinho(prod);  // ← CLICAR NA IMAGEM ADICIONA
                card.appendChild(img);

                const nome = document.createElement('div');
                nome.innerText = prod.nome;
                nome.style.fontWeight = 'bold';
                card.appendChild(nome);

                const preco = document.createElement('div');
                preco.innerText = `R$ ${prod.preco.toFixed(2)}`;
                card.appendChild(preco);

// 👉 Remova completamente o botão "Adicionar"

                container.appendChild(card);
            });
        });
}

function adicionarAoCarrinho(produto) {
    const existente = carrinho.find(p => p.id === produto.id);
    if (existente) {
        existente.quantidade++;
    } else {
        carrinho.push({ ...produto, quantidade: 1 });
    }
    atualizarCarrinho();
}

function atualizarCarrinho() {
    const container = document.getElementById('itens-carrinho');
    container.innerHTML = '';
    let total = 0;
    carrinho.forEach(item => {
        total += item.preco * item.quantidade;
        const div = document.createElement('div');
        div.innerHTML = `${item.nome} x${item.quantidade} - R$ ${(item.preco * item.quantidade).toFixed(2)}
            <button onclick='alterarQtd(${item.id}, -1)'>-</button>
            <button onclick='alterarQtd(${item.id}, 1)'>+</button>
            <button onclick='removerItem(${item.id})'>🗑️</button>`;
        container.appendChild(div);
    });
    document.getElementById('total-pedido').innerText = 'Total: R$ ' + total.toFixed(2);
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

function pagar(metodo) {
    if (carrinho.length === 0) {
        alert('Carrinho vazio');
        return;
    }
    fetch('/pix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ empresa_id, carrinho })
    })
    .then(res => res.json())
    .then(dados => {
        mostrarModalPix(dados.payload, dados.txid);
    });
}

function mostrarModalPix(payload, txid) {
    document.getElementById('qr-code').innerHTML = '<img src="https://api.qrserver.com/v1/create-qr-code/?data=' + encodeURIComponent(payload) + '&size=200x200">';
    document.getElementById('modal-pix').style.display = 'block';
    let tentativas = 0;
    const maxTentativas = 20;
    const intervalo = setInterval(() => {
        fetch('/verificar_pagamento/' + txid)
            .then(res => res.json())
            .then(status => {
                if (status.status === 'CONCLUIDO') {
                    document.getElementById('status-pagamento').innerText = '✔ Pagamento aprovado! Senha: TOTEM-' + status.senha;
                    clearInterval(intervalo);
                    carrinho = [];
                    atualizarCarrinho();
                    setTimeout(() => { location.reload(); }, 5000);
                }
            });
        tentativas++;
        if (tentativas >= maxTentativas) {
            clearInterval(intervalo);
        }
    }, 3000);
}

window.onload = () => {
    carregarCategorias();
};

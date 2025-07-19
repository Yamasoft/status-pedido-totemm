document.addEventListener('DOMContentLoaded', () => {
    carregarTotal();

    const urlParams = new URLSearchParams(window.location.search);
    const empresa_id = parseInt(urlParams.get('empresa_id'));

    let carrinho = [];
    let carrinhoSalvo = localStorage.getItem('carrinho_itens');

    if (carrinhoSalvo) {
        try {
            carrinho = JSON.parse(carrinhoSalvo);
        } catch (e) {
            console.error('Erro ao ler carrinho do LocalStorage:', e);
            carrinho = [];
        }
    }

    // BOTÃO PIX
    document.getElementById('btn-pix').onclick = () => {
        document.getElementById('area-manutencao').style.display = 'none';
        if (!empresa_id || carrinho.length === 0) {
            alert('Carrinho vazio ou empresa inválida!');
            return;
        }

        fetch('/pix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                empresa_id: empresa_id,
                carrinho: carrinho,
                metodo: 'pix'
            })
        })
        .then(res => res.json())
        .then(dados => {
            if (dados.erro) {
                mostrarErroPix();
                return;
            }

            const qr = dados.payload || dados.pixCopiaECola;
            const txid = dados.txid;

            document.getElementById('area-pix').style.display = 'block';

            document.getElementById('qr-code').innerHTML = `
                <div style="
                    display: inline-block;
                    border: 4px solid #1976D2;
                    border-radius: 10px;
                    padding: 8px;
                    background-color: #FFFFFF;
                ">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qr)}&size=220x220"
                         style="display:block; margin:auto;">
                </div>
            `;

            document.getElementById('status-pagamento').innerText = 'Aguardando pagamento...';

            let tempoRestante = 180;
            const statusDiv = document.getElementById('status-pagamento');
            const timerLabel = document.createElement('p');
            timerLabel.style.color = '#D32F2F';
            timerLabel.style.fontWeight = 'bold';
            timerLabel.style.marginTop = '10px';
            statusDiv.appendChild(timerLabel);

            function atualizarTimer() {
                const minutos = Math.floor(tempoRestante / 60);
                const segundos = tempoRestante % 60;
                timerLabel.innerText = `⏳ Tempo restante: ${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
                if (tempoRestante <= 0) {
                    clearInterval(contagem);
                    clearInterval(verificar);
                    alert('Tempo expirado! Voltando para os pedidos.');
                    localStorage.removeItem('total_carrinho');
                    localStorage.removeItem('carrinho_itens');
                    window.location.href = "/pedido?empresa_id=" + empresa_id;
                }
                tempoRestante--;
            }

            atualizarTimer();
            const contagem = setInterval(atualizarTimer, 1000);

            let pedidoFinalizado = false;

            const verificar = setInterval(() => {
                fetch('/verificar_pagamento/' + txid)
                    .then(res => res.json())
                    .then(status => {
                        if (status.status === 'CONCLUIDO' && !pedidoFinalizado) {
                            pedidoFinalizado = true;
                            clearInterval(verificar);
                            clearInterval(contagem);

                            fetch('/finalizar_pagamento', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    empresa_id: empresa_id,
                                    carrinho: carrinho,
                                    txid: txid
                                })
                            })
                            .then(r => r.json())
                            .then(resp => {
                                if (resp.status === 'ok') {
                                    document.getElementById('area-pix').style.display = 'none';
                                    document.querySelectorAll("button").forEach(btn => btn.style.display = "none");

                                    const confirmacaoDiv = document.createElement('div');
                                    confirmacaoDiv.style.cssText = `
                                        background-color: #E8F5E9;
                                        border: 3px solid #4CAF50;
                                        border-radius: 15px;
                                        padding: 20px;
                                        margin: 20px auto;
                                        max-width: 90%;
                                        color: #2E7D32;
                                        font-size: 28px;
                                        font-weight: bold;
                                        text-align: center;
                                    `;
                                    confirmacaoDiv.innerHTML = `
                                        ✅ Pagamento aprovado!<br>
                                        Sua senha: <span style="font-size: 44px; color: #D32F2F;">${resp.senha}</span>
                                    `;
                                    document.body.appendChild(confirmacaoDiv);

                                    const cabecalho = document.getElementById("cabecalho");
                                    if (cabecalho) cabecalho.style.display = "none";

                                    const urlStatus = `http://${window.location.hostname}:5000/status_pedido/${resp.senha}`;

                                    const infoDiv = document.createElement("div");
                                    infoDiv.style.cssText = `
                                        text-align: center;
                                        margin-top: 20px;
                                        background: #FFF7E6;
                                        padding: 20px;
                                    `;
                                    infoDiv.innerHTML = `
                                        <p style="font-size: 20px;">
                                            📷 Escaneie o QR Code abaixo para acompanhar o status do seu pedido:
                                        </p>
                                        <div style="margin: 20px;">
                                            <img src="https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(urlStatus)}&size=180x180"
                                                 alt="QR Code de acompanhamento" style="width: 180px;">
                                        </div>
                                    `;
                                    document.body.appendChild(infoDiv);

                                    const voltarBtn = document.createElement("button");
                                    voltarBtn.textContent = "↩️ Voltar à tela inicial";
                                    voltarBtn.style.cssText = `
                                        background-color: #1976D2;
                                        color: white;
                                        padding: 15px 30px;
                                        font-size: 22px;
                                        border: none;
                                        border-radius: 8px;
                                        margin: 10px auto 30px auto;
                                        display: block;
                                        cursor: pointer;
                                    `;
                                    voltarBtn.onclick = () => {
                                        window.location.href = "/empresas_web";
                                    };
                                    document.body.appendChild(voltarBtn);

                                    setTimeout(() => {
                                        window.location.href = "/empresas_web";
                                    }, 60000);

                                    localStorage.removeItem('total_carrinho');
                                    localStorage.removeItem('carrinho_itens');
                                } else {
                                    alert('Erro ao finalizar pagamento: ' + resp.erro);
                                }
                            });
                        }
                    })
                    .catch(err => console.error('Erro ao verificar status:', err));
            }, 3000);
        })
        .catch(err => {
            console.error('Erro ao comunicar com servidor:', err);
            mostrarErroPix();
        });
    };

    // BOTÕES restantes
    document.getElementById('btn-credito').onclick = () => mostrarManutencao('CRÉDITO');
    document.getElementById('btn-debito').onclick = () => mostrarManutencao('DÉBITO');
    document.getElementById('btn-voltar').onclick = () => {
        window.location.href = "/pedido?empresa_id=" + empresa_id;
    };
    document.getElementById('btn-cancelar').onclick = () => {
        localStorage.removeItem('total_carrinho');
        localStorage.removeItem('carrinho_itens');
        window.location.href = '/empresas_web';
    };
});

function mostrarManutencao(tipo) {
    document.getElementById('area-pix').style.display = 'none';
    const manutencao = document.getElementById('area-manutencao');
    manutencao.style.display = 'block';
    manutencao.innerHTML = `
        <div style="
            background-color: #FFF3E0;
            border: 3px solid #FF9800;
            border-radius: 12px;
            padding: 30px;
            margin: 20px auto;
            max-width: 90%;
            color: #BF360C;
            font-size: 22px;
            font-weight: bold;
            text-align: center;
        ">
            ⚠️ O módulo de pagamento por ${tipo} está em manutenção no momento.<br>
            Por favor, escolha outra forma de pagamento.
        </div>
    `;
}

function mostrarErroPix() {
    document.getElementById('area-pix').style.display = 'none';
    const manutencao = document.getElementById('area-manutencao');
    manutencao.style.display = 'block';
    manutencao.innerHTML = `
        <div style="
            background-color: #FFF3E0;
            border: 3px solid #FF9800;
            border-radius: 12px;
            padding: 30px;
            margin: 20px auto;
            max-width: 90%;
            color: #BF360C;
            font-size: 22px;
            font-weight: bold;
            text-align: center;
        ">
            ⚠️ O serviço de pagamento via PIX está temporariamente indisponível.<br>
            Por favor, tente novamente em instantes ou escolha outra forma de pagamento.
        </div>
    `;
}

function carregarTotal() {
    let total = localStorage.getItem('total_carrinho');
    document.getElementById('valor-total').innerText = total ? 'Total: R$ ' + total : 'Total: R$ 0,00';
}

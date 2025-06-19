// Inicializar máscaras e validações
document.addEventListener('DOMContentLoaded', function() {
    // Checkbox "Selecionar Todos"
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            document.querySelectorAll('.solicitacao-check').forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    // Máscara para campos monetários
    const moneyInputs = document.querySelectorAll('.money');
    moneyInputs.forEach(input => {
        IMask(input, {
            mask: 'R$ num',
            blocks: {
                num: {
                    mask: Number,
                    thousandsSeparator: '.',
                    radix: ',',
                    scale: 2,
                    padFractionalZeros: true,
                    normalizeZeros: true
                }
            }
        });
    });

    // Calcular percentual de economia
    const valorEstimado = document.getElementById('valor_estimado');
    const valorHomologado = document.getElementById('valor_homologado');
    const percentualEconomia = document.getElementById('percentual_economia');

    if (valorEstimado && valorHomologado) {
        function calcularEconomia() {
            const ve = parseFloat(valorEstimado.value.replace('R$', '').replace('.', '').replace(',', '.'));
            const vh = parseFloat(valorHomologado.value.replace('R$', '').replace('.', '').replace(',', '.'));
            
            if (ve && vh && ve > 0) {
                const economia = ((ve - vh) / ve) * 100;
                percentualEconomia.value = economia.toFixed(2) + '%';
            } else {
                percentualEconomia.value = '';
            }
        }

        valorEstimado.addEventListener('input', calcularEconomia);
        valorHomologado.addEventListener('input', calcularEconomia);
    }
});

function criarNovaTriagem() {
    const solicitacoesSelecionadas = Array.from(
        document.querySelectorAll('input.solicitacao-check:checked')
    ).map(cb => cb.value);

    if (solicitacoesSelecionadas.length === 0) {
        alert('Selecione pelo menos uma solicitação para criar a triagem');
        return;
    }

    const modal = new bootstrap.Modal(document.getElementById('modalNovaTriagem'));
    modal.show();
}

function salvarTriagem() {
    const form = document.getElementById('formNovaTriagem');
    const formData = new FormData(form);
    
    // Adicionar solicitações selecionadas
    const solicitacoesSelecionadas = Array.from(
        document.querySelectorAll('input.solicitacao-check:checked')
    ).map(cb => cb.value);
    
    formData.append('solicitacoes', JSON.stringify(solicitacoesSelecionadas));

    fetch('/solicitacao-compra/triagem/criar', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Erro ao criar triagem: ' + data.message);
        }
    })
    .catch(error => {
        alert('Erro ao processar requisição: ' + error);
    });
}

function visualizarDetalhes(solicitacaoId) {
    window.location.href = `/solicitacao-compra/detalhes/${solicitacaoId}`;
}

function editarTriagem(triagemId) {
    window.location.href = `/solicitacao-compra/triagem/${triagemId}/editar`;
}

function abrirModalProcesso(triagemId) {
    // Carregar dados da triagem
    fetch(`/solicitacao-compra/triagem/${triagemId}/dados`)
        .then(response => response.json())
        .then(data => {
            // Preencher campos do formulário com dados da triagem
            document.getElementById('objeto').value = data.titulo;
            document.getElementById('ano').value = new Date().getFullYear();
            
            // Abrir o modal
            const modal = new bootstrap.Modal(document.getElementById('modalCriarProcesso'));
            modal.show();
        })
        .catch(error => {
            alert('Erro ao carregar dados da triagem: ' + error);
        });
}

function salvarProcesso() {
    const form = document.getElementById('formCriarProcesso');
    
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
    }

    const formData = new FormData(form);
    
    fetch('/solicitacao-compra/triagem/processo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Processo criado com sucesso!');
            window.location.href = `/painel/visualizar/${data.processo_id}`;
        } else {
            alert('Erro ao criar processo: ' + data.message);
        }
    })
    .catch(error => {
        alert('Erro ao processar requisição: ' + error);
    });
}  

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

    // Selecionar/Deselecionar todas as solicitações
    const selecionarTodas = document.getElementById('selecionarTodas');
    if (selecionarTodas) {
        selecionarTodas.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('input[name="solicitacao"]');
            checkboxes.forEach(cb => cb.checked = this.checked);
        });
    }
});

function abrirModalTriagem() {
    const selecionadas = document.querySelectorAll('input[name="solicitacao"]:checked');
    if (selecionadas.length === 0) {
        alert('Selecione pelo menos uma solicitação para criar a triagem.');
        return;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('modalCriarTriagem'));
    modal.show();
}

function salvarTriagem() {
    // Pegar os valores dos campos
    const titulo = document.getElementById('titulo').value;
    const descricao = document.getElementById('descricao').value;
    
    // Pegar os IDs das solicitações selecionadas
    const solicitacoesSelecionadas = Array.from(
        document.querySelectorAll('input[name="solicitacao"]:checked')
    ).map(cb => cb.value);
    
    if (solicitacoesSelecionadas.length === 0) {
        alert('Selecione pelo menos uma solicitação para criar a triagem.');
        return;
    }

    // Criar objeto com os dados
    const dados = {
        titulo: titulo,
        descricao: descricao,
        solicitacoes: solicitacoesSelecionadas
    };

    // Enviar para o servidor
    fetch('/solicitacao-compra/criar_triagem', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify(dados)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na requisição');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Fechar o modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalCriarTriagem'));
            modal.hide();
            
            // Recarregar a página
            window.location.reload();
        } else {
            throw new Error(data.message || 'Erro ao criar triagem');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao criar triagem: ' + error.message);
    });
}

function visualizarDetalhes(solicitacaoId) {
    const modalBody = document.getElementById('detalhesConteudo');
    modalBody.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
    
    const modal = new bootstrap.Modal(document.getElementById('modalDetalhes'));
    modal.show();
    
    fetch(`/solicitacao-compra/detalhes/${solicitacaoId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro ao carregar detalhes');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                modalBody.innerHTML = data.html;
            } else {
                throw new Error(data.message || 'Erro ao carregar detalhes');
            }
        })
        .catch(error => {
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    ${error.message || 'Erro ao carregar detalhes da solicitação'}
                </div>
            `;
            console.error('Erro:', error);
        });
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

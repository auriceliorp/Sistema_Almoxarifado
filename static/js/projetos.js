// Configuração do SweetAlert2
const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true
});

// Variáveis globais
let modalNovoProjeto = null;
let btnSalvarProjeto = null;
let formNovoProjeto = null;

// Inicialização quando o documento estiver pronto
$(document).ready(function() {
    console.log('Script de projetos carregado');
    inicializarModal();
});

// Função para inicializar o modal e seus elementos
function inicializarModal() {
    console.log('Inicializando modal...');
    
    // Inicializa elementos do modal
    const modalElement = document.getElementById('novoProjeto');
    if (!modalElement) {
        console.error('Modal não encontrado!');
        return;
    }
    
    modalNovoProjeto = new bootstrap.Modal(modalElement);
    btnSalvarProjeto = $('#btnSalvarProjeto');
    formNovoProjeto = $('#formNovoProjeto');
    
    // Configura eventos
    btnSalvarProjeto.on('click', salvarProjeto);
    
    console.log('Modal inicializado com sucesso');
}

// Função chamada quando o iframe de projetos carrega
function projetosCarregado() {
    console.log('Projetos carregados');
    carregarProjetos();
}

// Função para abrir o modal de novo projeto
function abrirModalNovoProjeto() {
    console.log('Abrindo modal de novo projeto');
    if (!modalNovoProjeto) {
        console.error('Modal não inicializado!');
        inicializarModal();
    }
    modalNovoProjeto.show();
}

// Função para salvar projeto
function salvarProjeto() {
    console.log('Função salvarProjeto chamada');

    if (!formNovoProjeto || !formNovoProjeto[0]) {
        console.error('Formulário não encontrado!');
        return;
    }

    const formData = new FormData(formNovoProjeto[0]);
    const data = Object.fromEntries(formData.entries());
    
    // Validação básica
    if (!data.titulo || !data.area || !data.prioridade) {
        Toast.fire({
            icon: 'error',
            title: 'Por favor, preencha todos os campos obrigatórios'
        });
        return;
    }

    // Adiciona o status inicial
    data.status = 'A Fazer';
    
    // Desabilita o botão durante o salvamento
    btnSalvarProjeto.prop('disabled', true)
            .html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...');
    
    console.log('Dados a serem enviados:', data);

    // Faz a requisição para a API
    $.ajax({
        url: '/api/projetos',
        method: 'POST',
        contentType: 'application/json',
        headers: {
            'X-CSRF-TOKEN': $('input[name="csrf_token"]').val()
        },
        data: JSON.stringify(data),
        success: function(response) {
            console.log('Projeto salvo:', response);
            
            // Fecha o modal
            modalNovoProjeto.hide();
            
            // Limpa o formulário
            formNovoProjeto[0].reset();
            
            // Recarrega os projetos
            carregarProjetos();
            
            // Mostra mensagem de sucesso
            Toast.fire({
                icon: 'success',
                title: 'Projeto criado com sucesso!'
            });
        },
        error: function(xhr, status, error) {
            console.error('Erro:', error);
            Toast.fire({
                icon: 'error',
                title: xhr.responseJSON?.error || 'Erro ao criar projeto. Tente novamente.'
            });
        },
        complete: function() {
            // Reabilita o botão após o salvamento
            btnSalvarProjeto.prop('disabled', false).html('Salvar');
        }
    });
}

// Função para carregar projetos
function carregarProjetos() {
    const iframe = document.querySelector('#conteudo-projetos');
    if (!iframe) {
        console.error('Iframe não encontrado!');
        return;
    }
    
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
    
    const area = $(iframeDoc).find('#area').val();
    const prioridade = $(iframeDoc).find('#prioridade').val();
    
    $.ajax({
        url: `/api/projetos?area=${area}&prioridade=${prioridade}`,
        headers: {
            'X-CSRF-TOKEN': $('input[name="csrf_token"]').val()
        },
        success: function(projetos) {
            const aFazer = $(iframeDoc).find('#a-fazer');
            const emProgresso = $(iframeDoc).find('#em-progresso');
            const concluido = $(iframeDoc).find('#concluido');
            
            aFazer.empty();
            emProgresso.empty();
            concluido.empty();
            
            projetos.forEach(function(projeto) {
                const card = criarCardProjeto(projeto);
                switch(projeto.status) {
                    case 'A Fazer':
                        aFazer.append(card);
                        break;
                    case 'Em Progresso':
                        emProgresso.append(card);
                        break;
                    case 'Concluído':
                        concluido.append(card);
                        break;
                }
            });
        },
        error: function(xhr, status, error) {
            console.error('Erro:', error);
            Toast.fire({
                icon: 'error',
                title: 'Erro ao carregar projetos'
            });
        }
    });
}

// Função para criar card de projeto
function criarCardProjeto(projeto) {
    return $('<div>').addClass('card mb-2').html(`
        <div class="card-body">
            <h5 class="card-title">${projeto.titulo}</h5>
            <p class="card-text">${projeto.descricao || ''}</p>
            <div class="d-flex justify-content-between align-items-center">
                <span class="badge bg-${getPrioridadeClass(projeto.prioridade)}">${projeto.prioridade}</span>
                <small>${projeto.responsavel || 'Sem responsável'}</small>
            </div>
            <div class="mt-2">
                <select class="form-select form-select-sm" onchange="parent.atualizarStatus(${projeto.id}, this.value)">
                    <option value="A Fazer" ${projeto.status === 'A Fazer' ? 'selected' : ''}>A Fazer</option>
                    <option value="Em Progresso" ${projeto.status === 'Em Progresso' ? 'selected' : ''}>Em Progresso</option>
                    <option value="Concluído" ${projeto.status === 'Concluído' ? 'selected' : ''}>Concluído</option>
                </select>
            </div>
        </div>
    `);
}

// Função para obter classe de prioridade
function getPrioridadeClass(prioridade) {
    switch(prioridade) {
        case 'Alta': return 'danger';
        case 'Média': return 'warning';
        case 'Baixa': return 'info';
        default: return 'secondary';
    }
}

// Função para atualizar status do projeto
function atualizarStatus(projetoId, novoStatus) {
    $.ajax({
        url: `/api/projetos/${projetoId}`,
        method: 'PUT',
        contentType: 'application/json',
        headers: {
            'X-CSRF-TOKEN': $('input[name="csrf_token"]').val()
        },
        data: JSON.stringify({ status: novoStatus }),
        success: function(response) {
            carregarProjetos();
            Toast.fire({
                icon: 'success',
                title: 'Status atualizado com sucesso!'
            });
        },
        error: function(xhr, status, error) {
            console.error('Erro:', error);
            Toast.fire({
                icon: 'error',
                title: 'Erro ao atualizar status'
            });
            carregarProjetos(); // Recarrega para reverter mudanças visuais
        }
    });
} 

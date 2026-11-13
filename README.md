# Barbearia Brenner — Desktop offline (protótipo executável)

## Objetivo

Mesmos componentes, telas, cores, modais, tabelas e permissões do frontend React fornecido pelo projeto, em uma janela Windows com **pywebview/WebView2**, acompanhada por um serviço local em Python e **SQLite**. CustomTkinter não foi utilizado porque exigiria reconstruir a interface e não manteria fidelidade visual.

O servidor Django/PostgreSQL original continua sendo a fonte oficial após a sincronização. O **`backend_ref/` é apenas a cópia de referência do código enviado e não precisa ser publicado para iniciar o programa local**.

## Estrutura

```text
Brenner_Desktop_Offline/
├── frontend/                  # React original; nova aba Sincronização no modo desktop
│   ├── src/main.jsx
│   ├── src/style.css
│   ├── .env.desktop             # VITE_API_URL=/api
│   ├── package.json            # comando build:desktop
│   └── ...
├── desktop/
│   ├── app.py                  # servidor HTTP local e interface WebView
│   ├── engine.py               # API, cache, regras locais, fila e sincronização
│   ├── store.py                # banco SQLite, login local e token DPAPI
│   ├── selecionar.html         # escolha de painel, antes de abrir React
│   ├── config.example.json
│   ├── launcher.py
│   ├── INICIAR_ADMIN.ps1
│   ├── INICIAR_BALCAO.ps1
│   ├── TESTAR_SEM_JANELA.ps1
│   └── GERAR_EXE_WINDOWS.ps1
├── tests/                     # testes sem Django real
└── backend_ref/               # backend Django de referência, sem .env
```

## Rodar no VS Code (Windows)

Pré-requisitos: **Node.js 20+**, **Python 3.11+**, acesso inicial à API HTTPS do seu Django, e **Microsoft Edge WebView2 Runtime** no computador.

1. Abra esta pasta no VS Code e abra um terminal PowerShell.
2. No diretório raiz, instale dependências do Python:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r desktop\requirements.txt
```

Se o PowerShell bloquear a ativação de `.venv`, use `\.venv\Scripts\python.exe` no lugar de `python` ou configure a política de execução apenas para a sessão.

3. Faça o build desktop do React (este build é separado da versão web):

```powershell
cd frontend
npm ci
npm run build:desktop
cd ..
```

O build cria `frontend/dist/admin/index.html` e `frontend/dist/barbearia/index.html` e utiliza `VITE_API_URL=/api`, sem fazer requisições diretamente do navegador ao domínio Django.

4. Inicie o programa:

```powershell
python -m desktop.app
```

Na primeira execução, indique uma URL como `https://meu-dominio.com/api` (**não coloque `/` depois de `api`**). A configuração é salva em:

```text
%LOCALAPPDATA%\BrennerDesktop\config.json
```

A tela inicial permite escolher **Administração** ou **Balcão**. Ambas usam os seus formulários, ícones, CSS e autenticação já existentes no React.

Alternativas:

```powershell
python -m desktop.app --panel admin
python -m desktop.app --panel barbearia
python -m desktop.app --panel both
python -m desktop.app --serve
```

Com `--serve`, abra o endereço mostrado no terminal no navegador, útil para o Console F12 e depuração; não precisa de pywebview para esse teste. As rotas `/admin/` e `/barbearia/` funcionam no servidor local sem Nginx.

### Testar com sua API de desenvolvimento

No diretório raiz, com o Django já rodando:

```powershell
python -m desktop.app --serve --api http://127.0.0.1:8000/api
```

A primeira autenticação de cada usuário precisa acontecer **online** neste computador, para salvar uma verificação forte da senha, o perfil e a cópia inicial dos dados. Depois você pode desligar a internet, fechar o app, abrir de novo e autenticar offline com o mesmo e-mail/senha. Por padrão, uma autorização offline vale por **30 dias desde o último login online**; o número é ajustável em `config.json`:

```json
{
  "api_url": "https://meu-dominio.com/api",
  "offline_login_valid_days": 30
}
```

Enquanto há conexão, o aplicativo revalida a identidade com `/api/auth/me/` e atualiza dados automaticamente. **Não guarda senhas em texto nem tenta reenviá-las periodicamente.** No Windows, o token remoto persistido é protegido com DPAPI, vinculado ao usuário do Windows.

## Gerar `.exe` no Windows

Depois de compilar o React e instalar as dependências:

```powershell
.\desktop\GERAR_EXE_WINDOWS.ps1
```

Saída prevista:

```text
dist\BrennerDesktop.exe
```

A compilação de um **executável Windows precisa acontecer no Windows**. Não há `.exe` pré-compilado neste pacote; a compilação PyInstaller/WebView2 ainda deve ser validada no seu computador.

## Como funciona o SQLite

O programa cria automaticamente na primeira execução:

```text
%LOCALAPPDATA%\BrennerDesktop\brenner_offline.sqlite3
```

Ele guarda dados previamente baixados do servidor, registros novos, alterações locais, imagens sincronizáveis e fila de ações. Também cria a pasta `imagens/` e os metadados de sincronização. **Não precisa rodar `makemigrations` ou `migrate` no Django para este módulo desktop.**

As cópias de dados são separadas por usuário, respeitando o perfil admin ou balconista. As permissões são validadas novamente no Django ao enviar alterações.

### O que funciona na versão atual

- Login online e, após primeiro acesso, offline, por administrador ou balconista.
- Consultar cadastros e histórico já baixados do Django sem internet.
- Cadastrar e atualizar localmente produtos, clientes, serviços, barbeiros, agenda, folgas, despesas e vendas, de acordo com permissões.
- Registrar vendas sem conexão com responsável **Barbearia/Administração** (`barbeiro=null`) ou com barbeiro, e reduzir estoque local provisoriamente.
- Registrar/editar/cancelar/concluir agendamentos na base local, com envio posterior.
- Fila persistente de alterações, tentativas automáticas de envio a cada 30 segundos, envio manual e data/hora da última sincronização.
- Mensagens de erro/conflito que exigem conferência, sem substituir automaticamente dados atuais do servidor.
- Guardar fotos de produtos/barbeiros originadas do domínio do servidor e enviar novas imagens para ele pela fila.
- Financeiro offline com **totais provisórios**, calculados a partir do cache; relatórios Excel offline apenas se já foram baixados anteriormente.

### Restrições importantes — protótipo, não produção

1. **Não garantimos conciliação financeira completa entre várias máquinas desconectadas.** Um produto pode acabar no estoque ou um horário pode ser ocupado por outro aparelho. O Django pode recusar uma operação ao sincronizar; veja-a na aba *Sincronização*. A API Django original ainda não implementa contrato completo de sincronização por versão, idempotência persistida e resolução de conflitos.
2. **Não fechar meses offline.** Fechamentos financeiros são enviados somente online.
3. **A disponibilidade de horários depende de validação definitiva no Django.** A operação local pode ser aceita provisoriamente e recusada na sincronização.
4. **A API online é a autoridade** para valores, comissão, movimentos, estoque e regras de negócio. O cálculo local exibido antes da sincronização pode diferir; no Financeiro ele é marcado como provisório.
5. Ações cujo resultado ficou incerto durante o envio **não são reenviadas automaticamente**; confira no sistema online antes de clicar em *Tentar novamente*, para não duplicar vendas.
6. Arquivos/fontes e imagens externos a seu domínio que dependam da internet podem não ser exibidos offline. Os componentes React/CSS originais são preservados; fidelidade visual pixel a pixel exige que todas as fontes e imagens externas também estejam disponíveis localmente.
7. O banco SQLite guarda registros operacionais em texto no disco (senha não é guardada em texto); considere BitLocker, contas Windows individuais e backup. A revogação imediata de uma conta não pode ser garantida durante desconexão.
8. Primeira instalação **não cria uma cópia das informações sem um login inicial online**. Abra o painel conectado e confira o status *Última sincronização* antes de desconectar.
9. **Edição e exclusão de registros criados offline** e imagens dependentes de IDs temporários precisam ser testadas com a API real, incluindo campanhas de múltiplos usuários. Os testes simulados não cobrem todos os endpoints e regras particulares do Django.
10. Não altere a API Django nem publique este cliente offline em produção sem testes de concorrência, segurança e backups.

## Testes automatizados incluídos

Na raiz:

```powershell
python -m unittest discover -s tests -v
```

Os testes usam um servidor Django simulado e conferem rotas locais, login, cache, venda offline, fila, sincronização, conflito e persistência do banco após reinício. **Não substituem testes com PostgreSQL e a API publicada.**

## Correções recomendadas antes do uso real com dinheiro

- Adicionar ao Django endpoint de lote de sincronização com `operation_id` único e persistente, idempotência por operação e versões de registros (ETag/`updated_at`).
- Resolver conflitos de agenda e estoque com interface de escolha, não apenas a ação *Tentar novamente*.
- Validar conciliação de vendas e pagamentos após quedas de rede e interrupção do processo.
- Testar o empacotamento em Windows 10 e Windows 11 com WebView2 e os provedores de imagem/fontes do projeto.
- Testar offline/online de cada formulário e perfis com banco de homologação separado do banco de produção.

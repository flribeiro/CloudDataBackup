# CloudDataBackup
Programa para automação de backup de bases de dados em cloud storages.

O propósito da aplicação é automatizar a tarefa de fazer (e testar) o backup de bancos de dados, compactá-lo, fazer seu upload para um serviço de storage na nuvem e, por fim, enviar um e-mail de notificação com o relatório do processo para destinarário(s) especificado(s).

**Bancos de dados suportados (até o momento):**
* Firebird

**Cloud storages suportados (até o momento):**
* Amazon S3

## Instalação

Antes de tudo, é necessário ter Python instalado, na versão 3>.

Para download da aplicação, é necessário clonar o respositório git no seu sistema de arquivos local: 

```git clone https://github.com/flribeiro/CloudDataBackup .```

Este procedimento irá criar em seu sistema de arquivos local um diretório chamado "clouddatabackup". Sua primeira tarefa será instalar os requisitos para aplicação, e logo depois configurar a aplicação, o que deverá ser feito preenchendo todos os parâmetros do arquivo INI modelo, contido no repositório.

Para os requisitos, basta já ter o Python instalado e executar o seguinte comando (num prompt dentro do repositório local):

```pip install -r requirements.txt```

Aqui vai uma breve explicação de cada parâmetro do arquivo de configuração:

**[GERAL]**

**nome_cliente** - Nome do cliente proprietário da base de dados cujo backup será feito, a fim de identificar o mesmo.

**ip_servidor** - Endereço IP para conexão com o banco de dados. 

**fb_port** - Porta TCP para conexão com o banco de dados. Caso este parâmetro seja omitido, a aplicação assume que a porta a ser utilizada é a porta `3050`, ou seja, a porta padrão do Firebird SQL.

**dir_backup** - Diretório temporário para realização do backup.

**dir_bd** - Caminho do arquivo do banco de dados.

**user_fb** - Usuário para autenticação no banco de dados.

**pass_fb** - Senha para autenticação no banco de dados.

**[AWS]**

**aws_access_key_id** - ID da chave de acesso AWS para autenticação na AWS e utilização do serviço S3 (Simple Storage Service), para upload do backup.

**aws_secret_access_key** - Segredo da chave de acesso AWS, para autenticação na AWS.

**[E-mail]**

**mail_from** - Endereço de e-mail da conta que será utilizada como remetente.

**mail_user** - Nome de usuário para antenticação no servidor SMTP.

**mail_pass** - Senha para autenticação SMTP.

**mail_server** - Servidor SMTP.

**mail_port** - Porta para envio SMTP.

**mail_to** - Endereços de e-mail a serem notificados (separados por vírgula).

## Modo de usar

Para usar a aplicação, após instalação, usar o seguinte comando:

```python cldbkp.py```

Todo o procedimento será realizado, e os logs permanecerão no diretório especificado no parâmetro `dir_backup` do arquivo de configuração.
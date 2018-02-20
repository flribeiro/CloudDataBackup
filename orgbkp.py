# coding=UTF-8
import sys
import fdb
import datetime as dt
import lzma
import smtplib
import os
import boto3
import time as t
from configparser import ConfigParser
from email.mime.text import MIMEText
from fdb import services

__author__ = 'Fabricio L. Ribeiro'

''' Aplicação destinada a fazer backup da base de dados Firebird da Orgsystem
    Software, testar o restore e, se tudo estiver dentro dos conformes, faz
    a compactação do arquivo de backup usando o método 'lzma' e, por fim, 
    faz o upload do arquivo para um bucket no S3 da Amazon AWS.
    
    Tudo isso gerando um log que será enviado por e-mail para os interessados.
    
    Um arquivo de configuração é lido no diretório config/ da raiz da aplicação,
    a fim de parametrizar os dados particulares da execução.
'''

''' TODO: Criar classes para gerenciar log e conexão ao Firebird. '''

log = ''
var = dict()
con = ''


# Implementar classe pra gerenciar arquivo de log.
class ArquivoLog():
    pass


class Conf(object):
    def __init__(self, ini):
        self.__conf = ConfigParser()
        self.__ini = ini
        self.__conf.read(ini)
        self.__dconf = dict(self.__conf['GERAL'])
        self.__dawsconf = dict(self.__conf['AWS'])
        self.__dmailconf = dict(self.__conf['E-mail'])

    def geral(self, param):
        return self.__dconf[param]

    def aws(self, param):
        return self.__dawsconf[param]

    def mail(self, param):
        return self.__dmailconf[param]

    def __str__(self):
        return "Caminho do arquivo de inicialização: " + self.__ini


class ArquivoDeLog(object):
    def __init__(self, ini):
        print(ini.geral('user_fb'))
        self.__log = '\n\n|=====================< ' + now() + ' >=====================|\n' \
                          'Versão do Firebird: ' + conecta_firebird(ini).get_server_version() + '\n' \
                          'Usuario do banco de dados: ' + ini.geral('user_fb') + '\n' \
                          'IP do servidor: ' + ini.geral('ip_servidor') + '\n'
        self.registra_log('Processo iniciado.')

    def registra_log(self, msg):
        self.__log += now("hora") + ': ' + msg + '\n'

    def mostra_log(self):
        return self.__log

    def grava_arq_log(self):
        with open('orgbkp.log', 'a') as alog:
            alog.write(self.__log)
        self.rotaciona_arq_log()

    def rotaciona_arq_log(self):
        if os.stat('orgbkp.log').st_size > 5000000:
            try:
                nome_rotat = 'orgbkp' + now('a') + '.log'
                os.rename('orgbkp.log', nome_rotat)
            except IOError as e:
                msg = 'Houve um problema ao tentar efetuar a rotatividade do arquivo de log: ' + str(e)
                print(msg)
                self.registra_log(msg)


class ConexaoFB(object):
    __con, __cliente, __bd, __bkp, __cliente = ''

    def __init__(self, ip, usuario, senha, uribd, uribkp, cliente):
        try:
            self.__con = services.connect(
                host=ip,
                user=usuario,
                password=senha
            )
        except fdb.Error as e:
            msg = 'Houve um erro ao tentar conectar-se ao servidor de ' \
                  'banco de dados: {}.'.format(str(e))
            print(msg)
            # registrar log no objeto ArquivoDeLog
        self.__bd = uribd
        self.__bkp = uribkp + 'osbd.fbk'
        self.__cliente = cliente

    def backup(self):
        # Registrar início do backup no log
        try:
            self.__con.backup(self.__bd, self.__bkp, metadata_only=True, collect_garbage=False)
            self.__con.wait()
        except fdb.fbcore.DatabaseError as erro:
            msg = 'Houve um problema no backup: ' + str(erro)
            print(msg)
            # Registrar erro no log.
        # Registrar no log ('Backup concluído.')
        self.__con.readlines()

    def restore(self):
        # Registrar início do restore no log
        try:
            self.__con.restore(self.__bkp, self.__bkp + 'teste.fdb', replace=1)
            self.__con.wait()
        except fdb.fbcore.DatabaseError as erro:
            msg = 'Houve um problema no restore: ' + str(erro)
            print(msg)
            # Registra erro no log
        # Registra no log ('Restore concluído.')
        self.__con.readlines()


### DESCONTINUADA após implementação da classe ConexaoFB
# def conecta_firebird(ini):
#     global var, con
#     try:
#         con = services.connect(
#             host=ini.geral('ip_servidor'),
#             user=ini.geral('user_fb'),
#             password=ini.geral('pass_fb')
#         )
#     except fdb.Error as e:
#         msg = 'Houve um erro ao tentar conectar-se ao banco de dados: %s' % str(e)
#         print(msg)
#         # registra_log(msg)
#     return con


# def backup():
#     global var, con
#     arq_backup = var['dir_backup'] + 'osbd.fbk'
#     con = conecta_firebird()
#     registra_log('Iniciando backup.')
#     try:
#         con.backup(var['dir_bd'], arq_backup, metadata_only=True, collect_garbage=False)
#         con.wait()
#     except fdb.fbcore.DatabaseError as erro:
#         msg = 'Houve um problema no backup: ' + str(erro)
#         print(msg)
#         registra_log(msg)
#     registra_log('Backup concluído.')
#     return con.readlines()


# def restore():
#     global var
#     arq_backup = var['dir_backup'] + 'osbd.fbk'
#     con = conecta_firebird()
#     registra_log('Iniciando restore.')
#     try:
#         con.restore(arq_backup, var['dir_backup'] + 'teste.fdb', replace=1)
#         con.wait()
#     except fdb.fbcore.DatabaseError as erro:
#         msg = 'Houve um problema no restore: ' + str(erro)
#         print(msg)
#         registra_log(msg)
#     registra_log('Restore concluído.')
#     return con.readlines()


def nome_arquivo_datahora():
    global var
    txt = str(dt.datetime.now())
    txt = txt[0:13].replace(' ', '').replace('-', '') + '.7z'
    return str(var['nome_cliente']).replace(' ', '') + txt


def now(opc=''):
    data = str(dt.datetime.now())
    escolhas = {
        "ano": data[0:4],
        "mes": data[5:7],
        "dia": data[8:10],
        "hora": data[11:16],
        "": data[0:10],
    }
    return escolhas.get(opc, "")


def compacta_bkp():
    global var
    # subprocess.call(['7z', 'a', arq_7zip, arq_backup])
    arq_backup = var['dir_backup'] + 'osbd.fbk'
    arq_7zip = var['dir_backup'] + nome_arquivo_datahora()
    var['arq_7zip'] = nome_arquivo_datahora()
    arq_handler = open(arq_backup, 'rb')
    registra_log('Iniciando compactação.')
    with lzma.open(arq_7zip, "wb") as arqz:
        arqz.write(arq_handler.read())
    registra_log('Compactação concluída.')


def upload_to_s3():
    global var
    registra_log('Iniciando upload para S3.')
    session = boto3.Session(aws_access_key_id=var['aws_access_key_id'],
                            aws_secret_access_key=var['aws_secret_access_key'])
    print(session.get_available_resources())
    print(session.get_available_services())
    s3 = session.resource("s3")
    # s3 = session.client("s3")
    dados = open(var['dir_backup'] + var['arq_7zip'], 'rb')
    caminho = var['nome_cliente'] + '/' + now('ano') + '/' + now('mes') + '/' + now('dia') + '/' + var['arq_7zip']
    try:
        s3.Bucket('orgsystem.backup').put_object(Key=caminho, Body=dados)
        registra_log('Upload para S3 concluído.')
    except boto3.S3UploadFailedError as err:
        msg = 'Houve um problema no restore: ' + str(err)
        print(msg)
        registra_log(msg)


def notifica_email():
    global log
    global var

    msg = MIMEText(log)
    msg['Subject'] = 'OrgBKP: Notificação para %s' % var['nome_cliente']
    msg['From'] = var['mail_from']
    msg['To'] = var['mail_to']
    try:
        s = smtplib.SMTP(var['mail_server'] + ':' + var['mail_port'])
        s.starttls()
        s.login(var['mail_user'], var['mail_pass'])
        s.send_message(msg)
        s.quit()
    except smtplib.SMTPException as e:
        msg = 'Não foi possível enviar o e-mail de notificação. Favor verificar configurações de e-mail:' + str(e)
        print(msg)
        registra_log(msg)
        exit()
    registra_log('Notificação enviada para: ' + var['mail_to'] + '.')


def main(argv):
    global log
    global var

    # print('Argumentos:', str(argv))

    # instanciar parser config (ini)

    # instanciar ArquivoDeLog

    ### A inicialização do arquivo de log passou a ser feita no construtor
    ###    da classe ArquivoDeLog.
    # log = log + '\n\n|=====================< ' + now('ano') + ' >=====================|\n'
    # log = log + 'Versão do Firebird: ' + conecta_firebird().get_server_version() + '\n'
    # log = log + 'Usuario do banco de dados: ' + var['user_fb'] + '\n'
    # log = log + 'IP do servidor: ' + var['ip_servidor'] + '\n'
    # registra_log('Processo iniciado.')

    rel_backup = backup()
    rel_restore = restore()

    compacta_bkp()

    upload_to_s3()

    notifica_email()

    gera_arq_log()


def test(argv):
    # conf, awsconf, mailconf = parseconfig()
    ini = Conf('orgbkp.ini')
    print(ini.geral('ip_servidor'))
    alog = ArquivoDeLog(ini)
    print(alog.mostra_log())
    alog.registra_log("Teste.")
    alog.registra_log("Outra mensagem.")
    alog.registra_log("Última.")
    alog.grava_arq_log()
    # Testar conexão FB, métodos: backup e restore.


if __name__ == "__main__":
    ## main(sys.argv)
    test(sys.argv)

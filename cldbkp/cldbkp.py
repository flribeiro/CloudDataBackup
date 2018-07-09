# coding=UTF-8
import sys
import fdb
import datetime as dt
import lzma
import smtplib
import os
import boto3
import os.path
import argparse as ap
from boto3 import exceptions
from configparser import ConfigParser
from email.mime.text import MIMEText
from fdb import services

__author__ = 'Fabricio L. Ribeiro'
__version__ = '0.1'

''' Aplicação destinada a fazer backup da base de dados Firebird da Orgsystem
    Software, testar o restore e, se tudo estiver dentro dos conformes, faz
    a compactação do arquivo de backup usando o método 'lzma' e, por fim,
    faz o upload do arquivo para um bucket no S3 da Amazon AWS.

    Tudo isso gerando um log que será enviado por e-mail para os interessados.

    Um arquivo de configuração é lido no diretório config/ da raiz da aplicação,
    a fim de parametrizar os dados particulares da execução.
'''


class Conf:
    def __init__(self, arqini):
        self.__conf = ConfigParser()
        self.__ini = arqini
        self.__conf.read(arqini)
        self.__dconf = dict(self.__conf['GERAL'])
        self.__dawsconf = dict(self.__conf['AWS'])
        self.__dmailconf = dict(self.__conf['E-mail'])

    def geral(self, param):
        return self.__dconf[param]

    def aws(self, param):
        return self.__dawsconf[param]

    def mail(self, param):
        return self.__dmailconf[param]

    def set_conf(self, param, valor):
        if (param is not None) and (param != '') and (valor is not None) and (valor != ''):
            self.__dconf[param] = valor
            return True
        else:
            return False

    def __str__(self):
        return "Caminho do arquivo de inicialização: " + self.__ini


class ArquivoDeLog:
    def __init__(self, ini):

        con = ConexaoFB(ini.geral('ip_servidor'), ini.geral('user_fb'), ini.geral('pass_fb'),
                        ini.geral('dir_bd'), ini.geral('dir_backup'), ini.geral('nome_cliente'),
                        self)

        self.__log = '\n\n|=====================< ' + now() + ' >=====================|\n' \
            'Versão do Firebird: ' + con.versao_firebird() + '\n' \
            'Usuario do banco de dados: ' + ini.geral('user_fb') + \
            '\nIP do servidor: ' + ini.geral('ip_servidor') + '\n'

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


class ConexaoFB:
    __con, __cliente, __bd, __bkp, arqlog = '', '', '', '', ''

    def __init__(self, ip, usuario, senha, uribd, uribkp, cliente,
                 arqlog: ArquivoDeLog):
        self.__bd = uribd
        self.__bkp = uribkp + 'osbd.fbk'
        self.__cliente = cliente
        self.arqlog = arqlog
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
            self.arqlog.registra_log(msg)

    def backup(self):
        self.arqlog.registra_log('Backup iniciado.')
        try:
            self.__con.backup(self.__bd, self.__bkp, metadata_only=False, collect_garbage=False)
            self.__con.wait()
        except fdb.fbcore.DatabaseError as erro:
            msg = 'Houve um problema no backup: ' + str(erro)
            print(msg)
            self.arqlog.registra_log(msg)
        self.arqlog.registra_log('Backup concluído.')
        self.__con.readlines()

    def restore(self):
        self.arqlog.registra_log('Restore iniciado.')
        try:
            self.__con.restore(self.__bkp, 'teste.fdb', replace=1)
            self.__con.wait()
        except fdb.fbcore.DatabaseError as erro:
            msg = 'Houve um problema no restore: ' + str(erro)
            print(msg)
            self.arqlog.registra_log(msg)
        self.arqlog.registra_log('Restore concluído.')
        self.__con.readlines()

    def versao_firebird(self):
        return self.__con.get_server_version()


def nome_arquivo_final(ini):
    return ini.geral('nome_cliente').replace(' ', '') + now('nomearq')


def now(opc=''):
    data = str(dt.datetime.now())
    escolhas = {
        "ano": data[0:4],
        "mes": data[5:7],
        "dia": data[8:10],
        "hora": data[11:16],
        "nomearq": data[0:13].replace(' ', '').replace('-', '') + '.7z',
        "": data[0:10],
    }
    return escolhas.get(opc, "")


def compacta_bkp(ini: Conf, arqlog: ArquivoDeLog):
    # global var
    # subprocess.call(['7z', 'a', arq_7zip, arq_backup])
    arq_backup = ini.geral('dir_backup') + 'osbd.fbk'
    arq_7zip = ini.geral('dir_backup') + nome_arquivo_final(ini)
    ini.set_conf('arq_7zip', nome_arquivo_final(ini))
    if not os.path.isfile(arq_backup):
        arqlog.registra_log('Arquivo de backup não foi encontrado para compactação.')
        return False
    arq_handler = open(arq_backup, 'rb')
    arqlog.registra_log('Iniciando compactação.')
    with lzma.open(arq_7zip, "wb") as arqz:
        arqz.write(arq_handler.read())
    if os.path.isfile(arq_7zip):
        arqlog.registra_log('Compactação concluída.')
        return True
    else:
        arqlog.registra_log('Houve algum problema na compactação do arquivo de backup.')
        return False


def envia_s3(ini: Conf, alog: ArquivoDeLog):
    session = boto3.Session(aws_access_key_id=ini.aws('aws_access_key_id'),
                            aws_secret_access_key=ini.aws('aws_secret_access_key'))

    s3 = session.resource("s3")

    # TODO futuramente usar access key do próprio cliente pra subir o backup
    arq_zip_path = ini.geral('dir_backup') + ini.geral('arq_7zip')
    if not os.path.isfile(arq_zip_path):
        alog.registra_log('Arquivo de backup não foi compactado.')
        return False
    dados = open(arq_zip_path, 'rb')
    caminho = ini.geral('nome_cliente') + '/' + now('ano') + '/' + now('mes') + '/' + now('dia') \
        + '/' + ini.geral('arq_7zip')

    try:
        alog.registra_log('Iniciando upload para S3.')
        s3.Bucket('bucket-teste-flr').put_object(Key=caminho, Body=dados)
        alog.registra_log('Upload para S3 concluído.')
    except exceptions.S3UploadFailedError as err:
        msg = 'Houve um problema no restore: ' + str(err)
        print(msg)
        alog.registra_log(msg)

    return True


def notifica_email(ini: Conf, alog: ArquivoDeLog):
    msg = MIMEText(alog.mostra_log())
    msg['Subject'] = 'orgbkp: Notificação para %s' % ini.geral('nome_cliente')
    msg['From'] = ini.mail('mail_from')
    msg['To'] = ini.mail('mail_to')

    try:
        s = smtplib.SMTP(ini.mail('mail_server') + ':' + ini.mail('mail_port'))
        s.starttls()
        s.login(ini.mail('mail_user'), ini.mail('mail_pass'))
        s.send_message(msg)
        s.quit()
    except smtplib.SMTPException as e:
        msg = 'Não foi possível enviar o e-mail de notificação. Favor verificar configurações de e-mail:' + str(e)
        print(msg)
        alog.registra_log(msg)
        exit()
    alog.registra_log('Notificação enviada para: ' + ini.mail('mail_to') + '.')


def main(argv):
    ''' Padrão para arquivo de inicialização '''
    arqconfig = 'orgbkp.ini'
    parser = ap.ArgumentParser(prog='PyOrgBKP',
                               description='Aplicativo destinado a automatizar o backup, '
                                           'teste e upload do backup compactado de uma base '
                                           'de dados Firebird utilizada em sistemas da '
                                           'Orgsystem Software.',
                               epilog='Desnvolvido por Fabricio L. Ribeiro (contato@fabriciolribeiro.com), 2018.')
    parser.add_argument('--conf', '-c',
                        help='Estipula um arquivo de inicializacao avulso, \
                             caso nao haja um "orgbkp.ini" presente no \
                             diretorio base do script.',
                        type=str)
    args = parser.parse_args()
    d = dict(vars(args))

    ''' Se veio outro arquivo INI pela linha de comando... '''
    if d['conf'] is not None:
        if isfile(d['conf']):
            arqconfig = d['conf']
    ini = Conf(arqconfig)

    ''' Instancia objeto ArquivoDeLog '''
    alog = ArquivoDeLog(ini)

    ''' Instancia objeto ConexaoFB '''
    fb = ConexaoFB(
        ini.geral('ip_servidor'),
        ini.geral('user_fb'),
        ini.geral('pass_fb'),
        ini.geral('dir_bd'),
        ini.geral('dir_backup'),
        ini.geral('nome_cliente'),
        alog
    )

    ''' Efetua backup/restore '''
    fb.backup()
    fb.restore()

    ''' Compacta arquivo de backup '''
    s7zip = compacta_bkp(ini, alog)
    if not s7zip:
        alog.registra_log('Não foi possível compactar o arquivo.')
    else:
        alog.registra_log('Compactação do arquivo de backup: OK.')

    ''' Faz upload do arquivo para AWS S3 '''
    s3 = envia_s3(ini, alog)
    if not s3:
        alog.registra_log('Não foi possível enviar o backup para o S3.')
    else:
        alog.registra_log('Upload do backup para S3: OK.')

    ''' Envia notificação e grava log. '''
    notifica_email(ini, alog)
    alog.grava_arq_log()


if __name__ == "__main__":
    main(sys.argv)

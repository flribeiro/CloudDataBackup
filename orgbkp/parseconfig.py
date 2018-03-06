import sys
import configparser as cp


def main(argv):
    config = cp.ConfigParser()
    # config.default_section = 'GERAL'
    secoes = config.sections()
    print('parser recém-criado: ' + str(secoes))
    config.read('orgbkp_model.ini')
    secoes = config.sections()
    print('seções do ini lido: ' + str(secoes))
    for key in config['AWS']: print(key)
    print(config['AWS'].get('aws_access_key_id'))
    print(config['E-mail'].get('mail_user'))
    print(dict(config.items()))
    print(dict(config['GERAL'].items()))
    # print(config.defaults())


if __name__ == "__main__":
    main(sys.argv)
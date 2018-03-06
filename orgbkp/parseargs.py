import sys
import argparse as ap
import textwrap as tw


def main(argv):
    parser = ap.ArgumentParser(prog='PyOrgBKP',
                               description='Aplicativo destinado a automatizar o backup, '
                                           'teste e upload do backup compactado de uma base '
                                           'de dados Firebird utilizada em sistemas da '
                                           'Orgsystem Software.',
                               epilog='Desnvolvido por Fabricio L. Ribeiro (contato@fabriciolribeiro.com), 2018.')
    parser.add_argument('--conf', type=, )
    args = parser.parse_args()
    print(args.accumulate(args.inteiro))


if __name__ == '__main__':
    main(sys.argv)
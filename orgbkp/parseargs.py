import sys
import argparse as ap


def main(argv):
    parser = ap.ArgumentParser(description='Apenas um teste.',
                               epilog='Desnvolvido por Fabricio L. Ribeiro '
                                      '(contato@fabriciolribeiro.com)')
    parser.add_argument('inteiro', metavar='N', type=int, nargs='+',
                        help='um inteiro para o acumulador')
    parser.add_argument('--sum', dest='accumulate', action='store_const',
                        const=sum, default=max, help='soma os inteiros (padrão: acha '
                                                     'o max)')
    args = parser.parse_args()
    print(args.accumulate(args.inteiro))


if __name__ == '__main__':
    main(sys.argv)
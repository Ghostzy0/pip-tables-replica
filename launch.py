import argparse

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Original partial local data conversation replica')
    parser.add_argument('--smoke',help='Run synthetic controller/engine verification without UI')
    args=parser.parse_args()
    if args.smoke:
        from tables_replica.smoke import run
        run(args.smoke)
    else:
        from tables_replica.ui import main
        raise SystemExit(main())

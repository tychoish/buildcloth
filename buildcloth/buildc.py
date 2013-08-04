from stages import BuildSystemGenerator
from multiprocessing import cpu_count
import argparse
import os
import logging

log_level = logging.WARNING
logger = logging.getLogger(__name__)
logging.basicConfig(level=log_level)

def cli_ui():
    parser = argparse.ArgumentParser("'buildc' -- build system tool.")

    parser.add_argument('--log', '-l', action='store', default=False)
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--jobs', '-j', action='store', type=int, default=cpu_count)
    parser.add_argument('--file', '-f', action='append',
                        default=[os.path.join(os.getcwd(), 'buildc.yaml')])
    parser.add_argument('stages', nargs="*" action='store', default=None)
    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    elif args.log is not False:
        log_level = logging.INFO
    else:
        log_level = log_level

    if os.path.isdir(os.path.dirname(args.log)):
        logging.basicConfig(filename=args.log, level=log_level)
    else:
        logging.basicConfig(level=log_level)

    return args

def main():
    ui = cli_ui()

    if os.path.isdir('buildc') or os.path.exists('buildc.py'):
        try:
            from buildc import functions
        except ImportError:
            from buildc import funcs as functions
        else:
            functions = None
    else:
        functions = None

    bsg = BuildSystemGenerator(functions)
    bsg.system.workers(ui.jobs)

    for fn in ui.file:
        if fn.endswith('json'):
            bsg.system.ingest_json(fn)
        elif fn.endswith('yaml') or fn.endswith('yml'):
            bsg.system.ingest_yaml(fn)
        else:
            logger.warning('format of {0} is unclear, not parsing'.format(fn))

    bsg.finalize()

    if stages is None:
        bsg.system.run()
    else:
        highest_stage = 0

        for stage in ui.stages:
            idx = bsg.get_stage_index(stage)
            if idx > highest_stage:
                highest_stage = idx

        bsg.run_part(idx=highest_stage, strict=False)

if __name__ == '__main__':
    main()

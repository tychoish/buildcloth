import os
import subprocess
import argparse
import yaml
import sys

project_root = os.path.abspath(os.path.dirname(__file__))

master_conf = os.path.join(project_root, 'conf.yaml')

with open(master_conf, 'r') as f:
    conf = yaml.safe_load(f)

buildsystem = conf['paths']['buildsystem']

sys.path.append(os.path.join(buildsystem, 'utils'))

def bootstrap():
    repo = conf['system']['tools']

    if os.path.exists(buildsystem):
        import bootstrap_helper

        cmd = []

        if bootstrap_helper.reset_ref is not None:
            cmd.append(['git', 'reset', '--quiet', '--hard', bootstrap_helper.reset_ref])

        cmd.append(['git', 'pull', '--quiet', 'origin', 'master'])

        for c in cmd:
            p = subprocess.Popen(c, cwd=buildsystem)
            p.wait()
        print('[bootstrap]: updated git repository.')
    else:
        p = subprocess.Popen([ 'git', 'clone', repo, buildsystem])
        p.wait()

        import bootstrap_helper
        print('[bootstrap]: created buildsystem directory.')

    bootstrap_helper.init_fs(buildsystem)
    bootstrap_helper.bootstrap()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('op', nargs='?', choices=['clean', 'setup'], default='setup')
    ui = parser.parse_args()

    if ui.op == 'clean':
        try:
            import bootstrap_helper
            bootstrap_helper.clean_buildsystem(buildsystem, conf)
        except ImportError:
            exit('[bootstrap]: Buildsystem not installed.')
    else:
        bootstrap()

if __name__ == '__main__':
    main()

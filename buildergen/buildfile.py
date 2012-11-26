def print_output(list):
    for line in list:
        print(line)

def write_file(list, filename):
    with open(filename, 'w') as f:
        for line in list:
            f.write(line + '\n')


class BuildFileError(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        if self.msg is None:
            return "Error in handling BuildFile."
        else:
            return "Error: " + self.msg

class BuildFile(object):
    def __init__(self, buildfile=None):
        self.builder = { '_all' : [] }
        self.buildfile = self.builder['_all']

        if buildfile is None:
            pass
        elif type(buildfile) is list:
            for line in buildfile:
                if type(line) is list:
                    raise BuildFileError('Cannot instantiate BuildFile with nested list.')
                    break
                else:
                    self.builder['_all'].append(line)
        else:
            raise BuildFileError('Instantiated BuildFile object with malformed argument.')

    # the following method is used internally to constrcd uct and
    # maintain the internal representation of the buildfile.

    def _add_to_builder(self, data, block):
        if type(data) is not str:
            raise BuildFileError('Added malformed data to BuildFile.')
        else:
            if block is '_all':
                pass
            else:
                self.buildfile.append(data)

            if block in self.builder:
                self.builder[block].append(data)
            else:
                self.builder[block] = [data]

    # The following methods produce output for public use.

    def get_block(self, block='_all'):
        return self.builder[block]

    def print_content(self, block_order=['_all']):
        output = []

        for block in block_order:
            output.append(self.builder[block])

        output = [item for sublist in output for item in sublist]
        print_output(output)

    def print_block(self, block='all'):
        print_output(self.builder[block])

    def write(self, filename, block_order=['_all']):
        output = []

        for block in block_order:
            output.append(self.builder[block])

        output = [item for sublist in output for item in sublist]
        write_file(output, filename)

    def write_block(self, filename, block='_all'):
        write_file(self.builder[block], filename)

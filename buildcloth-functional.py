from buildrule import BuildRules, Rule
from buildergen import MakefileBuilder, NinjaFileBuilder

if __name__ == '__main__':
    db = BuildRules()

    foo = Rule()
    foo.name('migrate')
    foo.command('mv a b')
    foo.command('mv a b')
    foo.depfile('abcd.d')
    foo.restat()
    foo.description('a brave new world')

    bar = Rule()
    bar.name('compile')
    bar.command('cc a.o')
    bar.command('cc a.o')
    bar.command('cc a.o')
    bar.description('catch-22')

    db.add(foo.rule())
    db.add(bar.rule())
    
    from pprint import pprint

    pprint(db.rules)

    print()
    pprint(db.list_rules())

    print()
    db.output = 'make'
    m = MakefileBuilder(db.fetch('migrate'))
    m.print_content()

    print()
    db.output = 'ninja'
    n = NinjaFileBuilder(db.fetch('migrate'))
    n.print_content()

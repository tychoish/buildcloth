PYTHONBIN = python
output = build
modsrc = buildergen

.PHONY:embedded testpy2 testpy3 testpypy

test:testpy2 testpy3

testpy2:$(wildcard $(modsrc)*.py)
	@/usr/bin/python2 test.py
	@echo [test]: Python 2 tests complete.
testpy3:$(wildcard $(modsrc)*.py)
	@/usr/bin/python3 test.py
	@echo [test]: Python 3 tests complete.
testpypy:$(wildcard $(modsrc)*.py)
	@. ~/python/pypy/bin/activate; pypy test.py
	@echo [test]: PyPy tests complete.

$(output)/: 
	@mkdir $@
	@echo [build]: created $@

$(output)/makefile_builder.py:$(modsrc)/makefilegen.py $(output)/ $(modsrc)/buildfile.py bin/build_embedded.py
	@$(PYTHONBIN) bin/build_embedded.py $@ $<
	@echo [build]: created $@
$(output)/ninjafile_builder.py:$(modsrc)/ninjagen.py $(output)/ $(modsrc)/buildfile.py bin/build_embedded.py
	@$(PYTHONBIN) bin/build_embedded.py $@ $<
	@echo [build]: created $@
embedded:$(output)/makefile_builder.py $(output)/ninjafile_builder.py

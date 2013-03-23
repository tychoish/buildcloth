PYTHONBIN = python
output = build
modsrc = buildcloth


.PHONY:embedded testpy2 testpy3 testpypy

test:testpy2 testpy3

testpy2:$(wildcard $(modsrc)*.py)
	@/usr/bin/python2 test.py
	@echo [test]: Python 2 tests complete.
testpy3:$(wildcard $(modsrc)*.py)
	@/usr/bin/python3 test.py
	@echo [test]: Python 3 tests complete.
testpypy:$(wildcard $(modsrc)*.py)
	@. /usr/bin/virtualenvwrapper.sh; workon pypy; pypy test.py
	@echo [test]: PyPy tests complete.

$(output)/: 
	@mkdir $@
	@echo [build]: created $@

$(output)/makecloth.py:$(modsrc)/makefile.py $(output)/ $(modsrc)/cloth.py bin/build_embedded.py
	@$(PYTHONBIN) bin/build_embedded.py $@ $<
	@echo [build]: created $@
$(output)/ninjacloth.py:$(modsrc)/ninja.py $(output)/ $(modsrc)/cloth.py bin/build_embedded.py
	@$(PYTHONBIN) bin/build_embedded.py $@ $<
	@echo [build]: created $@
embedded:$(output)/makecloth.py $(output)/ninjacloth.py

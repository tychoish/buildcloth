PYTHONBIN = python
output = build
modsrc = buildergen

.PHONY:embedded testpy2 testpy3

test:testpy2 testpy3

testpy2:$(wildcard $(modsrc)*.py)
	@/usr/bin/python2 test.py
	@echo [test]: Python 2 tests complete.
testpy3:$(wildcard $(modsrc)*.py)
	@/usr/bin/python3 test.py
	@echo [test]: Python 3 tests complete.

$(output)/: 
	@mkdir $@
	@echo [build]: created $@

$(output)/makefile_builder.py:$(output)/ $(modsrc)/buildfile.py $(modsrc)/makefilegen.py bin/build_embeded.py
	@$(PYTHONBIN) bin/build_embeded.py $@
	@echo [build]: created $@
embedded:test $(output)/makefile_builder.py

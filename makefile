PYTHONBIN = python
output = build
modsrc = buildcloth

tags:
	@find buildcloth -name "*.py" | grep -v "\.\#" | etags --output TAGS -
	@echo [dev]: regenerated tags


.PHONY:embedded testpy2 testpy3 testpypy docs

test:testpy

test-all: testpy2 testpy3 # testpypy

testpy:$(wildcard $(modsrc)*.py)
	@python test.py
	@echo [test]: Python tests complete.
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

docs:
	@$(MAKE) -C docs/ html
stage-docs:
	@$(MAKE) -C ../institute/ stage push
push-docs:
	@$(MAKE) -C ../institute/ publish push
release:all
	python setup.py sdist upload
	@$(MAKE) -C ../institute/ stage push

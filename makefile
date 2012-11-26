PYTHONBIN = python
output = build
modsrc = buildergen

.PHONY:embeded

test:$(wildcard $(modsrc)*.py)
	@$(PYTHONBIN) test.py

$(output)/: 
	@mkdir $@
	@echo [build]: created $@

$(output)/makefile_builder.py:$(output)/ $(modsrc)/buildfile.py $(modsrc)/makefilegen.py bin/build_embeded.py
	@$(PYTHONBIN) bin/build_embeded.py $@
	@echo [build]: created $@
embeded:test $(output)/makefile_builder.py

MAKEFILEARGS += -j 

#
# Publication system
#

all:intersphinx html
setup: 
	@true
clean: 
	-rm -rf build/*


include makefile.docs
include bin/makefile.compatibility 

publish: $(BUILDDIR)/publish
$(BUILDDIR)/dirhtml:dirhtml
$(BUILDDIR)/publish:$(BUILDDIR)/dirhtml
	@mkdir -p $@
	@rsync -ra $</ $@/
	@touch $@
	@echo "[build]: migrated '$<' to '$@'"

-include $(BUILDDIR)/makefile.intersphinx
$(BUILDDIR)/makefile.intersphinx:bin/intersphinx.py bin/makefile_builder.py $(BUILDDIR) conf.py
	@$(PYTHONBIN) $< $@

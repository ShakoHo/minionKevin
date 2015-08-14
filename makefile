# Pull all dependencies for minionKevin

kevin-env = kevin-env
virtual-env-exists = $(shell if [ -d "kevin-env" ]; then echo "exists"; fi)

install: virtual-env activate lib-install

virtual-env:
ifneq ($(virtual-env-exists),exists)
	@virtualenv ${kevin-env}
else
	@echo "virtual environment exists." 
endif

lib-install: virtual-env
	$(shell if [ -z "$$VIRTUAL_ENV" ]; then\
			 . ./kevin-env/bin/activate;\
		fi;\
		pip install jenkinsapi 1>&2 2> /dev/null;)

activate: virtual-env
	$(shell if [ -z "$$VIRTUAL_ENV" ]; then\
			 . ./kevin-env/bin/activate;\
		fi;)

clean:
	@rm -rf ${kevin-env}

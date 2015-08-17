# Pull all dependencies for minionKevin

install: venv lib-install

venv:
ifndef VIRTUAL_ENV
		virtualenv kevin-env
endif

lib-install:
		. kevin-env/bin/activate; \
		pwd;\
		pip install jenkinsapi;

clean:
		rm -rf kevin-env


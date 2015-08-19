# Pull all dependencies for minionKevin

install: venv lib-install

venv:
ifndef VIRTUAL_ENV
		virtualenv kevin-env
endif

lib-install:
		. kevin-env/bin/activate; \
		python setup.py install;

clean:
		rm -rf kevin-env


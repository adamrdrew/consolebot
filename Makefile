clean:
	rm -rf build dist *.egg-info

install:
	python -m spacy download en_core_web_md
	mkdir data



test:
	python -m unittest discover .

coverage:
	coverage run -m unittest discover .
	coverage report -m
	coverage xml

install-build-deps:
	pip install build twine wheel

build-app: clean
	python setup.py sdist bdist_wheel
install:
	python -m spacy download en_core_web_md
	mkdir data

test:
	python -m unittest discover -s tests -p '*.py'
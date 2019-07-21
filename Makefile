clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {}

clean-build:
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive __pycache__/
	rm --force --recursive *.egg-info

build: clean-build
	pyi-makespec  --onefile lastseen.py
	pyinstaller -F --onefile --clean -y --dist ./dist/linux --workpath /tmp lastseen.spec

lint:
	# autopep8 -i *.py
	autopep8 -i *.py
	flake8
	#for when I'm a masochist
	#pylint *.py

test: clean-pyc
	py.test --verbose --color=yes $(TEST_PATH)


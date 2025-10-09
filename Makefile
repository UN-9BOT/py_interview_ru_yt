.PHONY: readme

readme: test2.json generate_readme.py
	python generate_readme.py

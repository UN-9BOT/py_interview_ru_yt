.PHONY: readme add all clean test

readme: list.json generate_readme.py
	python generate_readme.py

add:
	python add_video.py && $(MAKE) readme

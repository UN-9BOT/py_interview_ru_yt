.PHONY: readme add all clean test

readme: test2.json generate_readme.py
	python generate_readme.py

add:
	python add_video.py && $(MAKE) readme

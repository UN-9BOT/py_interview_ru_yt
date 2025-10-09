.PHONY: readme add

readme: generate_readme.py
	python generate_readme.py

add:
	python add_video.py && $(MAKE) readme

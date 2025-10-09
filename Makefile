.PHONY: readme add meta

ifeq ($(firstword $(MAKECMDGOALS)),meta)
  ifeq ($(strip $(LINK)),)
    LINK := $(word 2,$(MAKECMDGOALS))
  endif
  ifneq ($(strip $(LINK)),)
    MAKECMDGOALS := meta
  endif
endif

readme: generate_readme.py
	python generate_readme.py

add:
	python add_video.py && $(MAKE) readme

meta:
ifndef LINK
	$(error Укажите ссылку: make meta "https://www.youtube.com/watch?v=..." или make meta LINK=...)
endif
	python get_meta_from_yt_link.py "$(LINK)"

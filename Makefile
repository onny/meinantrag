all: build

build:
	@if [ -f package-lock.json ]; then npm ci; else npm install; fi
	npm run build

install:
	mkdir -p $(DESTDIR)
	cp -r assets $(DESTDIR)/ 
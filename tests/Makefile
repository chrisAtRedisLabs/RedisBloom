all: test test-cuckoo test-perf

PYTHON:=python

test: unittests flowtests

flowtests:
	$(PYTHON) tdigest.py
	$(PYTHON) pytests.py
	$(PYTHON) cuckoo.py
	$(PYTHON) cms.py
	$(PYTHON) topk.py
	$(PYTHON) init_test.py

unittests: test-basic test-cuckoo
	./test-basic
	./test-cuckoo

perf: test-perf
	time ./test-perf

CPPFLAGS:=$(CPPFLAGS) -I$(ROOT)/src 
CFLAGS:=$(CFLAGS)
LDFLAGS = -lm -lc

test-basic: test-basic.o $(DEPS_TEST)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test-cuckoo: test-cuckoo.o $(DEPS_TEST)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^ $(LDFLAGS)

test-perf: test-perf.o $(DEPS_TEST)
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^ $(LDFLAGS)

build-test: test-basic test-perf test-cuckoo

clean:
	$(RM) test-basic *.o *.rdb *.pyc
	$(RM) -fr *.dSYM

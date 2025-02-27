###############################################################################
# Compiler settings
###############################################################################
CC := gcc
CFLAGS := -Wall -Wextra -Wpedantic -Werror -std=c11

CXX := g++
CXXFLAGS := -Wall -Wextra -Wpedantic -Werror -std=c++17

BUILD_DIR := build

###############################################################################
# Google Test settings
###############################################################################
GTEST_DIR := googletest/googletest
GTEST_SRC_DIR := $(GTEST_DIR)/src
GTEST_HEADERS := $(GTEST_DIR)/include/gtest/*.h $(GTEST_DIR)/include/gtest/internal/*.h
GTEST_BUILD_DIR := $(BUILD_DIR)/gtest
GTEST_ALL_OBJ  := $(GTEST_BUILD_DIR)/gtest-all.o
GTEST_MAIN_OBJ := $(GTEST_BUILD_DIR)/gtest_main.o
GTEST_MAIN_A   := $(GTEST_BUILD_DIR)/gtest_main.a

###############################################################################
# Python venv
###############################################################################
VENV_DIR := build/venv
PYTEST = $(VENV_DIR)/bin/pytest

###############################################################################
# Источники приложения
###############################################################################
APP_SRC := src/main.c

# Все тестовые .cpp
TEST_SRCS := \
    tests/unit/unit_test_positive.cpp \
    tests/unit/unit_test_negative.cpp

###############################################################################
# Цели по умолчанию
###############################################################################
.PHONY: all clean run-int run-float run-unit-test run-integration-tests venv clone-gtest clang-format

all: clone-gtest clang-format build/app.exe build/unit-tests.exe

clean:
	@echo "Cleaning..."
	rm -rf $(BUILD_DIR)/
	rm -rf tests/integration/__pycache__
	rm -rf .pytest_cache

###############################################################################
# clone gtest (если отсутствует)
###############################################################################
clone-gtest:
	@if [ ! -d "googletest" ]; then \
	  echo "Cloning googletest..."; \
	  git clone https://github.com/google/googletest; \
	fi
	@if [ ! -f "$(GTEST_SRC_DIR)/gtest-all.cc" ]; then \
	  echo "Error: gtest-all.cc not found!"; \
	  exit 1; \
	fi

###############################################################################
# clang-format
###############################################################################
clang-format:
	@echo "Running clang-format..."
	find . -regex '.*\.\(h\|c\|cpp\)$$' -exec clang-format -i {} +

###############################################################################
# Сборка приложения (app.exe)
###############################################################################
build/app.exe: $(APP_SRC)
	@echo "Building app.exe"
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $^

###############################################################################
# Сборка test-версии приложения: app-test.o (без main(), с -DUNIT_TEST)
###############################################################################
build/app-test.o: $(APP_SRC)
	@echo "Building app-test.o with -DUNIT_TEST"
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -DUNIT_TEST -DGTEST -c $< -o $@ -g

###############################################################################
# Сборка Google Test (gtest-all.o, gtest_main.o, gtest_main.a)
###############################################################################
$(GTEST_ALL_OBJ): $(GTEST_SRC_DIR)/gtest-all.cc $(GTEST_HEADERS)
	@echo "Building gtest-all.o"
	@mkdir -p $(GTEST_BUILD_DIR)
	$(CXX) $(CXXFLAGS) -isystem $(GTEST_DIR)/include -I$(GTEST_DIR) -c $< -o $@

$(GTEST_MAIN_OBJ): $(GTEST_SRC_DIR)/gtest_main.cc $(GTEST_HEADERS)
	@echo "Building gtest_main.o"
	@mkdir -p $(GTEST_BUILD_DIR)
	$(CXX) $(CXXFLAGS) -isystem $(GTEST_DIR)/include -I$(GTEST_DIR) -c $< -o $@

$(GTEST_MAIN_A): $(GTEST_ALL_OBJ) $(GTEST_MAIN_OBJ)
	@echo "Archiving gtest_main.a"
	ar rcs $@ $^

###############################################################################
# Построим общий unit-tests.exe из всех .cpp-тестов, gtest_main.a, app-test.o
###############################################################################
build/unit-tests.exe: $(GTEST_MAIN_A) build/app-test.o $(TEST_SRCS)
	@echo "Building unit-tests.exe (all tests in one)"
	$(CXX) $(CXXFLAGS) -isystem $(GTEST_DIR)/include -pthread \
		$(TEST_SRCS) build/app-test.o $(GTEST_MAIN_A) \
		-o $@

###############################################################################
# Запуск приложения
###############################################################################
run-int: build/app.exe
	@echo "Running in integer mode"
	@./build/app.exe

run-float: build/app.exe
	@echo "Running in float mode"
	@./build/app.exe --float

###############################################################################
# Запуск юнит-тестов (единый бинарник)
###############################################################################
run-unit-test: build/unit-tests.exe
	@echo "Running unit-tests.exe..."
	@./build/unit-tests.exe

###############################################################################
# Python venv + integration tests
###############################################################################
venv:
	@echo "Creating virtual environment $(VENV_DIR)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
	  python3 -m venv $(VENV_DIR); \
	  $(VENV_DIR)/bin/pip install --upgrade pip pytest; \
	fi

run-integration-tests: build/app.exe venv tests/integration/test_math.py
	@echo "Running integration tests with pytest..."
	@. $(VENV_DIR)/bin/activate && $(VENV_DIR)/bin/pytest tests/integration/test_math.py

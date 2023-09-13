#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.nz>
#
# SPDX-License-Identifier: MIT

dist: test license-check setup-sdist

test:
	python -m unittest

license-check:
	reuse lint

setup-sdist:
	python setup.py sdist

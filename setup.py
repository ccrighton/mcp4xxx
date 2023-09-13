# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.nz>
#
# SPDX-License-Identifier: MIT
from setuptools import setup

setup(
    name="mcp4xxx",
    version="1.0.0",
    description="Control a Microchip MCP4XXX digital potentiometer with Micropython",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    project_urls={
        "GitHub": "https://bitbucket/ccrighton/mcp4xxx"
    },
    author="Charlie Crighton",
    maintainer="Charlie Crighton",
    maintainer_email="code@crighton.nz",
    license="MIT",
    license_files="LICENSES",
    py_modules=["mcp4xxx"]
)

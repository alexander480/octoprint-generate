# coding=utf-8
from setuptools import setup
import octoprint_setuptools

setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
    identifier="generate",
    package="octoprint_generate",
    name="OctoPrintGenerate",
    version="0.1.0",
    description="Integrates text-to-3D and image-to-3D model APIs within OctoPrint",
    author="Alexander Lester",
    requires=["requests"]
)

setup(**setup_parameters)

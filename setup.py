from setuptools import setup, find_packages
from pathlib import Path
setup(name='step-response-tools', version='0.1.0', packages=find_packages(exclude=['test']),
      description='Offline, unit-independent single-step response analysis',
      long_description=Path(__file__).with_name('README.md').read_text(encoding='utf-8'),
      long_description_content_type='text/markdown',
      url='https://github.com/PyLoT-Robotics/step-response-tools',
      python_requires='>=3.10', license='Apache-2.0',
      extras_require={'test': ['pytest']},
      entry_points={'console_scripts': ['step-response = step_response_tools.cli:main']})

from setuptools import setup, find_packages
import pathlib

VERSION = "1.0"

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(name="xiaomi-mijia2",
      version=VERSION,
      license="MIT License",
      description="A module to get info from Xiaomi Mijia2 Lywsd03mmc "
      "temperature and humidity sensor",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://gitlab.kcsni.ru/tango-deviceservers/xiaomi-mijia2-lywsd03mmc",
      author="Andrey Pechnikov",
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering :: Synchrotron",
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 3 :: Only",
          "Operating System :: Linux",
      ],
      py_modules=["xiaomi_mijia2"],
      package_dir={"": "xiaomi"},
      packages=find_packages(where="xiaomi"),
      python_requires=">=3.7",
      install_requires=["btmgmt>=1.1.0",
                        "lywsd03mmc>=0.1.0",
                        "pytango>=9.0.0"],
      include_package_data=True,
      zip_safe=False,
      entry_points={
            "console_scripts": [
                "XiaomiBluetooth=xiaomi_mijia2:main",
            ],
        },
      )

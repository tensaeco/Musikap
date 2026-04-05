name: Build APK

on:
  push:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v3

    - name: Build with Buildozer
      uses: ArtemSBulgakov/buildozer-action@v1
      with:
        command: buildozer -v android debug

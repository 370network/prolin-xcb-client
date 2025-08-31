{ lib, fetchFromGitHub, python3Packages, source ? null, ... }:

python3Packages.buildPythonApplication rec {
  pname = "prolin-xcb-client";
  version = "1.0";
  pyproject = true;

  src = if source != null then source else fetchFromGitHub {
    owner = "370network";
    repo = "prolin-xcb-client";
    rev = "61df6e569a0f448dce29ca916853dda96e6f3285";
    hash = "sha256-V2hPQKNrIDPbgt8NLHO9LeSm09rA96//KTnEiR2/rYQ=";
  };

  build-system = with python3Packages; [
    setuptools
  ];

  dependencies = with python3Packages; [
    m2crypto
    pyserial
    libusb1
  ];

  meta = with lib; {
    homepage = "https://github.com/370network/prolin-xcb-client";
    description = "prolin-xcb-client";
    license = licenses.asl20; # No idea but python adb lib is apache 2.0
    platforms = platforms.unix;
    maintainers = [];
  };
}

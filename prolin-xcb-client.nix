{ lib, fetchFromGitHub, python3Packages, source ? null, ... }:

python3Packages.buildPythonApplication rec {
  pname = "prolin-xcb-client";
  version = "1.0";
  pyproject = true;

  src = if source != null then source else fetchFromGitHub {
    owner = "370network";
    repo = "prolin-xcb-client";
    rev = "19002ce22ddd46a871e5054248147c53077fe3c1";
    hash = "sha256-QhodG8N51hRgXg/Kz4FHEXWbo8kbnnVD3rq5cD0owwk=";
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

{ buildPythonPackage, fetchPypi
, cryptography
, flake8
, coverage
, mock
, nose
}:

buildPythonPackage rec {
    pname = "http_ece";
    version = "1.0.5";
    src = fetchPypi {
      inherit pname version;
      sha256 = "1k06843n5q1rp3wh8qx1akl9lmcsvl2p1qxi9a9w581i1ija0c9g";
    };
    checkInputs = [
      flake8
      coverage
      mock
      nose
    ];
    doCheck = false; # pytest-runner is missing

    propagatedBuildInputs = [
      cryptography
    ];
}

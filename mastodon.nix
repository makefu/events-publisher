{ buildPythonPackage, callPackage, fetchPypi
, requests
, dateutil
, six
, pytz
, decorator
, cryptography
}:
buildPythonPackage rec {
    pname = "Mastodon.py";
    version = "1.3.1";
    src = fetchPypi {
      inherit pname version;
      sha256 = "1xih3wq47ki5wxm04v4haqnxc38hvnkx28yrmpyr02klw8s0y01z";
    };
    prePatch = ''
      sed -i 's/pytest-runner//' setup.py
    '';
    checkInputs = [
    ];
    doCheck = false; # missing pytest-runner
    propagatedBuildInputs = [
      requests
      dateutil
      six
      pytz
      decorator
      (callPackage ./http_ece.nix {})
    ];
}

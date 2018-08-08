{ buildPythonPackage, callPackage, fetchFromGitHub
, requests
}:
buildPythonPackage rec {
    pname = "facebook-sdk";
    version = "2018-07-24";
    src = fetchFromGitHub {
      owner =  "mobolic";
      repo = pname;
      rev = "3348fb9d02fc2fdfebf6e5b45f1aad06f532730f";
      sha256 = "0dh6ki6nc3w1gnc6p7a5hvza5fqnpl83ff004xk7rb0lpk1mwnyl";
    };
    doCheck = false; # missing pytest-runner
    propagatedBuildInputs = [
      requests
    ];
}
